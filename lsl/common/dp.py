# -*- coding: utf-8 -*-

"""
Module that contains common values found in the DP ICD, revision I.  The values 
are:
  * f_S - Sampleng rate in samples per second
  * T - Slot duration in seconds
  * T_2 - Sub-slot duration
  * N_MAX_UDP - Maximum UDP packet size
  
Also included are two functions to convert between frequencies and DP tuning 
words and functions for calculating the magnitude response of the TBN and DRX 
filters and a software version of DP.
"""

import numpy
from scipy.signal import freqz, lfilter
from scipy.interpolate import interp1d


__version__ = '0.5'
__revision__ = '$Rev$'
__all__ = ['fS', 'T', 'T2', 'N_MAX', 'freq2word', 'word2freq', 'delaytoDPD', 'DPDtodelay', 'gaintoDPG', 'DPGtogain', 'tbnFilter', 'drxFilter', 'SoftwareDP', '__version__', '__revision__', '__all__']

fS = 196.0e6	# Hz
T = 1.0		# seconds
T2 = 0.010	# seconds
N_MAX = 8192	# bytes

# CIC Filters
## TBN CIC filter #7 with order 2, decimation by 98
_tbnCIC7 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 
			27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 
			51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 
			75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 
			97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87, 86, 85, 84, 83, 82, 81, 80, 79, 78, 77, 76, 75, 74, 
			73, 72, 71, 70, 69, 68, 67, 66, 65, 64, 63, 62, 61, 60, 59, 58, 57, 56, 55, 54, 53, 52, 51, 50, 
			49, 48, 47, 46, 45, 44, 43, 42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 
			25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
## TBN CIC filter #6 with order 2, decimation by 196
_tbnCIC6 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 
			28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 
			52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 
			76, 77, 78, 79, 80, 81, 82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 
			100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 
			120, 121, 122, 123, 124, 125, 126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 
			140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 
			160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 
			180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 195, 194, 193, 
			192, 191, 190, 189, 188, 187, 186, 185, 184, 183, 182, 181, 180, 179, 178, 177, 176, 175, 174, 173, 
			172, 171, 170, 169, 168, 167, 166, 165, 164, 163, 162, 161, 160, 159, 158, 157, 156, 155, 154, 153, 
			152, 151, 150, 149, 148, 147, 146, 145, 144, 143, 142, 141, 140, 139, 138, 137, 136, 135, 134, 133, 
			132, 131, 130, 129, 128, 127, 126, 125, 124, 123, 122, 121, 120, 119, 118, 117, 116, 115, 114, 113, 
			112, 111, 110, 109, 108, 107, 106, 105, 104, 103, 102, 101, 100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 
			90, 89, 88, 87, 86, 85, 84, 83, 82, 81, 80, 79, 78, 77, 76, 75, 74, 73, 72, 71, 70, 69, 68, 67, 66, 
			65, 64, 63, 62, 61, 60, 59, 58, 57, 56, 55, 54, 53, 52, 51, 50, 49, 48, 47, 46, 45, 44, 43, 42, 41, 
			40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 
			15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
## TBN CIC filter #5 with order 2, decimation by 392
_tbnCIC5 = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 
			30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 
			56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81, 
			82, 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 103, 104, 105, 106, 
			107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124, 125, 126, 127, 
			128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 
			149, 150, 151, 152, 153, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 
			170, 171, 172, 173, 174, 175, 176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 
			191, 192, 193, 194, 195, 196, 197, 198, 199, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211, 
			212, 213, 214, 215, 216, 217, 218, 219, 220, 221, 222, 223, 224, 225, 226, 227, 228, 229, 230, 231, 232, 
			233, 234, 235, 236, 237, 238, 239, 240, 241, 242, 243, 244, 245, 246, 247, 248, 249, 250, 251, 252, 253, 
			254, 255, 256, 257, 258, 259, 260, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 272, 273, 274, 
			275, 276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 293, 294, 295, 
			296, 297, 298, 299, 300, 301, 302, 303, 304, 305, 306, 307, 308, 309, 310, 311, 312, 313, 314, 315, 316, 
			317, 318, 319, 320, 321, 322, 323, 324, 325, 326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 
			338, 339, 340, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350, 351, 352, 353, 354, 355, 356, 357, 358, 
			359, 360, 361, 362, 363, 364, 365, 366, 367, 368, 369, 370, 371, 372, 373, 374, 375, 376, 377, 378, 379, 
			380, 381, 382, 383, 384, 385, 386, 387, 388, 389, 390, 391, 392, 391, 390, 389, 388, 387, 386, 385, 384, 
			383, 382, 381, 380, 379, 378, 377, 376, 375, 374, 373, 372, 371, 370, 369, 368, 367, 366, 365, 364, 363, 
			362, 361, 360, 359, 358, 357, 356, 355, 354, 353, 352, 351, 350, 349, 348, 347, 346, 345, 344, 343, 342, 
			341, 340, 339, 338, 337, 336, 335, 334, 333, 332, 331, 330, 329, 328, 327, 326, 325, 324, 323, 322, 321, 
			320, 319, 318, 317, 316, 315, 314, 313, 312, 311, 310, 309, 308, 307, 306, 305, 304, 303, 302, 301, 300, 
			299, 298, 297, 296, 295, 294, 293, 292, 291, 290, 289, 288, 287, 286, 285, 284, 283, 282, 281, 280, 279, 
			278, 277, 276, 275, 274, 273, 272, 271, 270, 269, 268, 267, 266, 265, 264, 263, 262, 261, 260, 259, 258, 
			257, 256, 255, 254, 253, 252, 251, 250, 249, 248, 247, 246, 245, 244, 243, 242, 241, 240, 239, 238, 237, 
			236, 235, 234, 233, 232, 231, 230, 229, 228, 227, 226, 225, 224, 223, 222, 221, 220, 219, 218, 217, 216, 
			215, 214, 213, 212, 211, 210, 209, 208, 207, 206, 205, 204, 203, 202, 201, 200, 199, 198, 197, 196, 195, 
			194, 193, 192, 191, 190, 189, 188, 187, 186, 185, 184, 183, 182, 181, 180, 179, 178, 177, 176, 175, 174, 
			173, 172, 171, 170, 169, 168, 167, 166, 165, 164, 163, 162, 161, 160, 159, 158, 157, 156, 155, 154, 153, 
			152, 151, 150, 149, 148, 147, 146, 145, 144, 143, 142, 141, 140, 139, 138, 137, 136, 135, 134, 133, 132, 
			131, 130, 129, 128, 127, 126, 125, 124, 123, 122, 121, 120, 119, 118, 117, 116, 115, 114, 113, 112, 111, 
			110, 109, 108, 107, 106, 105, 104, 103, 102, 101, 100, 99, 98, 97, 96, 95, 94, 93, 92, 91, 90, 89, 88, 87, 
			86, 85, 84, 83, 82, 81, 80, 79, 78, 77, 76, 75, 74, 73, 72, 71, 70, 69, 68, 67, 66, 65, 64, 63, 62, 61, 60, 
			59, 58, 57, 56, 55, 54, 53, 52, 51, 50, 49, 48, 47, 46, 45, 44, 43, 42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 
			32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6, 5, 
			4, 3, 2, 1]

## DRX CIC filter #7 with order 5, decimation by 5
_drxCIC7 = drxCIC7 = [1, 5, 15, 35, 70, 121, 185, 255, 320, 365, 381, 365, 320, 255, 185, 121, 70, 35, 15, 5, 1]
## DRX CIC filter #6 with order 5, decimation by 10
_drxCIC6 = [1, 5, 15, 35, 70, 126, 210, 330, 495, 715, 996, 1340, 1745, 2205, 2710, 3246, 3795, 4335, 4840, 5280, 
			5631, 5875, 6000, 6000, 5875, 5631, 5280, 4840, 4335, 3795, 3246, 2710, 2205, 1745, 1340, 996, 715, 
			495, 330, 210, 126, 70, 35, 15, 5, 1]
## DRX CIC filter #5 with order 5, decimation by 20
_drxCIC5 = [1, 5, 15, 35, 70, 126, 210, 330, 495, 715, 1001, 1365, 1820, 2380, 3060, 3876, 4845, 5985, 7315, 8855, 
			10621, 12625, 14875, 17375, 20125, 23121, 26355, 29815, 33485, 37345, 41371, 45535, 49805, 54145, 
			58515, 62871, 67165, 71345, 75355, 79135, 82631, 85795, 88585, 90965, 92905, 94381, 95375, 95875, 
			95875, 95375, 94381, 92905, 90965, 88585, 85795, 82631, 79135, 75355, 71345, 67165, 62871, 58515, 
			54145, 49805, 45535, 41371, 37345, 33485, 29815, 26355, 23121, 20125, 17375, 14875, 12625, 10621, 
			8855, 7315, 5985, 4845, 3876, 3060, 2380, 1820, 1365, 1001, 715, 495, 330, 210, 126, 70, 35, 15, 5, 1]
## DRX CIC filter #4 with order 5, decimation by 49
_drxCIC4 = [1, 5, 15, 35, 70, 126, 210, 330, 495, 715, 1001, 1365, 1820, 2380, 3060, 3876, 4845, 5985, 7315, 8855, 
			10626, 12650, 14950, 17550, 20475, 23751, 27405, 31465, 35960, 40920, 46376, 52360, 58905, 66045, 73815, 
			82251, 91390, 101270, 111930, 123410, 135751, 148995, 163185, 178365, 194580, 211876, 230300, 249900, 
			270725, 292820, 316226, 340980, 367115, 394660, 423640, 454076, 485985, 519380, 554270, 590660, 628551, 
			667940, 708820, 751180, 795005, 840276, 886970, 935060, 984515, 1035300, 1087376, 1140700, 1195225, 
			1250900, 1307670, 1365476, 1424255, 1483940, 1544460, 1605740, 1667701, 1730260, 1793330, 1856820, 
			1920635, 1984676, 2048840, 2113020, 2177105, 2240980, 2304526, 2367620, 2430135, 2491940, 2552900, 
			2612876, 2671725, 2729300, 2785460, 2840070, 2893001, 2944130, 2993340, 3040520, 3085565, 3128376, 
			3168860, 3206930, 3242505, 3275510, 3305876, 3333540, 3358445, 3380540, 3399780, 3416126, 3429545, 
			3440010, 3447500, 3452000, 3453501, 3452000, 3447500, 3440010, 3429545, 3416126, 3399780, 3380540, 
			3358445, 3333540, 3305876, 3275510, 3242505, 3206930, 3168860, 3128376, 3085565, 3040520, 2993340, 
			2944130, 2893001, 2840070, 2785460, 2729300, 2671725, 2612876, 2552900, 2491940, 2430135, 2367620, 
			2304526, 2240980, 2177105, 2113020, 2048840, 1984676, 1920635, 1856820, 1793330, 1730260, 1667701, 
			1605740, 1544460, 1483940, 1424255, 1365476, 1307670, 1250900, 1195225, 1140700, 1087376, 1035300, 
			984515, 935060, 886970, 840276, 795005, 751180, 708820, 667940, 628551, 590660, 554270, 519380, 485985, 
			454076, 423640, 394660, 367115, 340980, 316226, 292820, 270725, 249900, 230300, 211876, 194580, 178365, 
			163185, 148995, 135751, 123410, 111930, 101270, 91390, 82251, 73815, 66045, 58905, 52360, 46376, 40920, 
			35960, 31465, 27405, 23751, 20475, 17550, 14950, 12650, 10626, 8855, 7315, 5985, 4845, 3876, 3060, 2380, 
			1820, 1365, 1001, 715, 495, 330, 210, 126, 70, 35, 15, 5, 1]
## DRX CIC filter #3 with order 5, decimation by 98
_drxCIC3 = [1, 5, 15, 35, 70, 126, 210, 330, 495, 715, 1001, 1365, 1820, 2380, 3060, 3876, 4845, 5985, 7315, 8855, 
			10626, 12650, 14950, 17550, 20475, 23751, 27405, 31465, 35960, 40920, 46376, 52360, 58905, 66045, 73815, 
			82251, 91390, 101270, 111930, 123410, 135751, 148995, 163185, 178365, 194580, 211876, 230300, 249900, 
			270725, 292825, 316251, 341055, 367290, 395010, 424270, 455126, 487635, 521855, 557845, 595665, 635376, 
			677040, 720720, 766480, 814385, 864501, 916895, 971635, 1028790, 1088430, 1150626, 1215450, 1282975, 
			1353275, 1426425, 1502501, 1581580, 1663740, 1749060, 1837620, 1929501, 2024785, 2123555, 2225895, 
			2331890, 2441626, 2555190, 2672670, 2794155, 2919735, 3049501, 3183545, 3321960, 3464840, 3612280, 
			3764376, 3921225, 4082925, 4249570, 4421250, 4598051, 4780055, 4967340, 5159980, 5358045, 5561601, 
			5770710, 5985430, 6205815, 6431915, 6663776, 6901440, 7144945, 7394325, 7649610, 7910826, 8177995, 
			8451135, 8730260, 9015380, 9306501, 9603625, 9906750, 10215870, 10530975, 10852051, 11179080, 11512040, 
			11850905, 12195645, 12546226, 12902610, 13264755, 13632615, 14006140, 14385276, 14769965, 15160145, 
			15555750, 15956710, 16362951, 16774395, 17190960, 17612560, 18039105, 18470501, 18906650, 19347450, 
			19792795, 20242575, 20696676, 21154980, 21617365, 22083705, 22553870, 23027726, 23505135, 23985955, 
			24470040, 24957240, 25447401, 25940365, 26435970, 26934050, 27434435, 27936951, 28441420, 28947660, 
			29455485, 29964705, 30475126, 30986550, 31498775, 32011595, 32524800, 33038176, 33551505, 34064565, 
			34577130, 35088970, 35599851, 36109535, 36617780, 37124340, 37628965, 38131401, 38631390, 39128670, 
			39622975, 40114035, 40601576, 41085320, 41564985, 42040285, 42510930, 42976626, 43437085, 43892025, 
			44341170, 44784250, 45221001, 45651165, 46074490, 46490730, 46899645, 47301001, 47694570, 48080130, 
			48457465, 48826365, 49186626, 49538050, 49880445, 50213625, 50537410, 50851626, 51156105, 51450685, 
			51735210, 52009530, 52273501, 52526985, 52769850, 53001970, 53223225, 53433501, 53632690, 53820690, 
			53997405, 54162745, 54316626, 54458970, 54589705, 54708765, 54816090, 54911626, 54995325, 55067145, 
			55127050, 55175010, 55211001, 55235005, 55247010, 55247010, 55235005, 55211001, 55175010, 55127050, 
			55067145, 54995325, 54911626, 54816090, 54708765, 54589705, 54458970, 54316626, 54162745, 53997405, 
			53820690, 53632690, 53433501, 53223225, 53001970, 52769850, 52526985, 52273501, 52009530, 51735210, 
			51450685, 51156105, 50851626, 50537410, 50213625, 49880445, 49538050, 49186626, 48826365, 48457465, 
			48080130, 47694570, 47301001, 46899645, 46490730, 46074490, 45651165, 45221001, 44784250, 44341170, 
			43892025, 43437085, 42976626, 42510930, 42040285, 41564985, 41085320, 40601576, 40114035, 39622975, 
			39128670, 38631390, 38131401, 37628965, 37124340, 36617780, 36109535, 35599851, 35088970, 34577130, 
			34064565, 33551505, 33038176, 32524800, 32011595, 31498775, 30986550, 30475126, 29964705, 29455485, 
			28947660, 28441420, 27936951, 27434435, 26934050, 26435970, 25940365, 25447401, 24957240, 24470040, 
			23985955, 23505135, 23027726, 22553870, 22083705, 21617365, 21154980, 20696676, 20242575, 19792795, 
			19347450, 18906650, 18470501, 18039105, 17612560, 17190960, 16774395, 16362951, 15956710, 15555750, 
			15160145, 14769965, 14385276, 14006140, 13632615, 13264755, 12902610, 12546226, 12195645, 11850905, 
			11512040, 11179080, 10852051, 10530975, 10215870, 9906750, 9603625, 9306501, 9015380, 8730260, 8451135, 
			8177995, 7910826, 7649610, 7394325, 7144945, 6901440, 6663776, 6431915, 6205815, 5985430, 5770710, 
			5561601, 5358045, 5159980, 4967340, 4780055, 4598051, 4421250, 4249570, 4082925, 3921225, 3764376, 
			3612280, 3464840, 3321960, 3183545, 3049501, 2919735, 2794155, 2672670, 2555190, 2441626, 2331890, 
			2225895, 2123555, 2024785, 1929501, 1837620, 1749060, 1663740, 1581580, 1502501, 1426425, 1353275, 
			1282975, 1215450, 1150626, 1088430, 1028790, 971635, 916895, 864501, 814385, 766480, 720720, 677040, 
			635376, 595665, 557845, 521855, 487635, 455126, 424270, 395010, 367290, 341055, 316251, 292825, 270725, 
			249900, 230300, 211876, 194580, 178365, 163185, 148995, 135751, 123410, 111930, 101270, 91390, 82251, 
			73815, 66045, 58905, 52360, 46376, 40920, 35960, 31465, 27405, 23751, 20475, 17550, 14950, 12650, 
			10626, 8855, 7315, 5985, 4845, 3876, 3060, 2380, 1820, 1365, 1001, 715, 495, 330, 210, 126, 70, 35, 
			15, 5, 1]

# FIR Filters
## Default beamformer delay FIR filters
_delayFIRs = [[0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 32767, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0], 
			[-15, 16, -41, 45, -89, 99, -168, 196, -308, 385, -605, 904, -1896, 32515, 2148, -1051, 630, -477, 316, -267, 171, -152, 90, -82, 42, -39, 15, -15, 0, 0, 0, 0], 
			[-30, 32, -81, 88, -173, 193, -327, 381, -597, 744, -1163, 1719, -3513, 31851, 4515, -2128, 1263, -949, 627, -528, 339, -301, 177, -162, 83, -77, 30, -29, 0, 0, 0, 0], 
			[-43, 46, -117, 127, -249, 278, -472, 547, -857, 1063, -1656, 2422, -4833, 30791, 7060, -3191, 1875, -1398, 922, -773, 496, -439, 259, -237, 120, -113, 44, -42, 0, 0, 0, 0],
			[-55, 58, -148, 161, -315, 351, -595, 689, -1079, 1332, -2069, 2995, -5845, 29362, 9737, -4202, 2441, -1806, 1189, -993, 637, -563, 331, -303, 154, -144, 56, -53, 0, 0, 0, 0], 
			[-64, 68, -174, 188, -369, 410, -695, 801, -1254, 1543, -2388, 3424, -6549, 27594, 12494, -5118, 2937, -2157, 1416, -1179, 756, -666, 392, -357, 182, -170, 66, -63, 0, 0, 0, 0], 
			[-71, 75, -192, 208, -407, 452, -766, 881, -1379, 1689, -2606, 3701, -6950, 25528, 15277, -5900, 3342, -2436, 1595, -1323, 848, -745, 439, -399, 203, -189, 74, -70, 0, 0, 0, 0], 
			[-75, 79, -203, 220, -430, 476, -808, 926, -1448, 1766, -2719, 3826, -7062, 23211, 18030, -6508, 3636, -2628, 1717, -1419, 908, -796, 469, -426, 217, -202, 79, -75, 0, 0, 0, 0], 
			[-76, 81, -206, 223, -436, 482, -818, 935, -1461, 1775, -2725, 3801, -6906, 20693, 20693, -6906, 3801, -2725, 1775, -1461, 935, -818, 482, -436, 223, -206, 81, -76, 0, 0, 0, 0], 
			[-75, 79, -202, 217, -426, 469, -796, 908, -1419, 1717, -2628, 3636, -6508, 18030, 23211, -7062, 3826, -2719, 1766, -1448, 926, -808, 476, -430, 220, -203, 79, -75, 0, 0, 0, 0], 
			[-70, 74, -189, 203, -399, 439, -745, 848, -1323, 1595, -2436, 3342, -5900, 15277, 25528, -6950, 3701, -2606, 1689, -1379, 881, -766, 452, -407, 208, -192, 75, -71, 0, 0, 0, 0], 
			[-63, 66, -170, 182, -357, 392, -666, 756, -1179, 1416, -2157, 2937, -5118, 12494, 27594, -6549, 3424, -2388, 1543, -1254, 801, -695, 410, -369, 188, -174, 68, -64, 0, 0, 0, 0], 
			[-53, 56, -144, 154, -303, 331, -563, 637, -993, 1189, -1806, 2441, -4202, 9737, 29362, -5845, 2995, -2069, 1332, -1079, 689, -595, 351, -315, 161, -148, 58, -55, 0, 0, 0, 0], 
			[-42, 44, -113, 120, -237, 259, -439, 496, -773, 922, -1398, 1875, -3191, 7060, 30791, -4833, 2422, -1656, 1063, -857, 547, -472, 278, -249, 127, -117, 46, -43, 0, 0, 0, 0], 
			[-29, 30, -77, 83, -162, 177, -301, 339, -528, 627, -949, 1263, -2128, 4515, 31851, -3513, 1719, -1163, 744, -597, 381, -327, 193, -173, 88, -81, 32, -30, 0, 0, 0, 0], 
			[-15, 15, -39, 42, -82, 90, -152, 171, -267, 316, -477, 630, -1051, 2148, 32515, -1896, 904, -605, 385, -308, 196, -168, 99, -89, 45, -41, 16, -15, 0, 0, 0, 0]]


## TBN FIR filter with decimation of 20
_tbnFIR = [-2.7370000000000000e+003,  5.3100000000000000e+002,  5.1600000000000000e+002, 
			 5.2100000000000000e+002,  5.4300000000000000e+002,  5.7900000000000000e+002, 
			 6.2500000000000000e+002,  6.7900000000000000e+002,  7.3800000000000000e+002, 
			 7.9800000000000000e+002,  8.5800000000000000e+002,  9.1500000000000000e+002, 
			 9.6600000000000000e+002,  1.0090000000000000e+003,  1.0420000000000000e+003, 
			 1.0620000000000000e+003,  1.0680000000000000e+003,  1.0570000000000000e+003, 
			 1.0280000000000000e+003,  9.8000000000000000e+002,  9.1100000000000000e+002, 
			 8.2000000000000000e+002,  7.1100000000000000e+002,  5.7400000000000000e+002, 
			 4.2100000000000000e+002,  2.4700000000000000e+002,  5.1000000000000000e+001, 
			-1.6300000000000000e+002, -3.9200000000000000e+002, -6.3400000000000000e+002,
			-8.8600000000000000e+002, -1.1450000000000000e+003, -1.4080000000000000e+003, 
			-1.6710000000000000e+003, -1.9300000000000000e+003, -2.1790000000000000e+003, 
			-2.4140000000000000e+003, -2.6290000000000000e+003, -2.8200000000000000e+003,
			-2.9820000000000000e+003, -3.1100000000000000e+003, -3.1990000000000000e+003, 
			-3.2440000000000000e+003, -3.2410000000000000e+003, -3.1860000000000000e+003, 
			-3.0730000000000000e+003, -2.9030000000000000e+003, -2.6710000000000000e+003, 
			-2.3740000000000000e+003, -2.0130000000000000e+003, -1.5850000000000000e+003, 
			-1.0920000000000000e+003, -5.3200000000000000e+002,  9.0000000000000000e+001, 
			 7.7500000000000000e+002,  1.5170000000000000e+003,  2.3140000000000000e+003, 
			 3.1600000000000000e+003,  4.0510000000000000e+003,  4.9800000000000000e+003, 
			 5.9410000000000000e+003,  6.9270000000000000e+003,  7.9290000000000000e+003, 
			 8.9400000000000000e+003,  9.9520000000000000e+003,  1.0955000000000000e+004, 
			 1.1943000000000000e+004,  1.2904000000000000e+004,  1.3831000000000000e+004, 
			 1.4715000000000000e+004,  1.5549000000000000e+004,  1.6323000000000000e+004, 
			 1.7032000000000000e+004,  1.7668000000000000e+004,  1.8225000000000000e+004, 
			 1.8698000000000000e+004,  1.9082000000000000e+004,  1.9373000000000000e+004, 
			 1.9569000000000000e+004,  1.9667000000000000e+004,  1.9667000000000000e+004, 
			 1.9569000000000000e+004,  1.9373000000000000e+004,  1.9082000000000000e+004, 
			 1.8698000000000000e+004,  1.8225000000000000e+004,  1.7668000000000000e+004, 
			 1.7032000000000000e+004,  1.6323000000000000e+004,  1.5549000000000000e+004, 
			 1.4715000000000000e+004,  1.3831000000000000e+004,  1.2904000000000000e+004, 
			 1.1943000000000000e+004,  1.0955000000000000e+004,  9.9520000000000000e+003, 
			 8.9400000000000000e+003,  7.9290000000000000e+003,  6.9270000000000000e+003, 
			 5.9410000000000000e+003,  4.9800000000000000e+003,  4.0510000000000000e+003, 
			 3.1600000000000000e+003,  2.3140000000000000e+003,  1.5170000000000000e+003, 
			 7.7500000000000000e+002,  9.0000000000000000e+001, -5.3200000000000000e+002, 
			-1.0920000000000000e+003, -1.5850000000000000e+003, -2.0130000000000000e+003, 
			-2.3740000000000000e+003, -2.6710000000000000e+003, -2.9030000000000000e+003, 
			-3.0730000000000000e+003, -3.1860000000000000e+003, -3.2410000000000000e+003, 
			-3.2440000000000000e+003, -3.1990000000000000e+003, -3.1100000000000000e+003, 
			-2.9820000000000000e+003, -2.8200000000000000e+003, -2.6290000000000000e+003, 
			-2.4140000000000000e+003, -2.1790000000000000e+003, -1.9300000000000000e+003, 
			-1.6710000000000000e+003, -1.4080000000000000e+003, -1.1450000000000000e+003, 
			-8.8600000000000000e+002, -6.3400000000000000e+002, -3.9200000000000000e+002, 
			-1.6300000000000000e+002,  5.1000000000000000e+001,  2.4700000000000000e+002, 
			 4.2100000000000000e+002,  5.7400000000000000e+002,  7.1100000000000000e+002, 
			 8.2000000000000000e+002,  9.1100000000000000e+002,  9.8000000000000000e+002, 
			 1.0280000000000000e+003,  1.0570000000000000e+003,  1.0680000000000000e+003, 
			 1.0620000000000000e+003,  1.0420000000000000e+003,  1.0090000000000000e+003, 
			 9.6600000000000000e+002,  9.1500000000000000e+002,  8.5800000000000000e+002, 
			 7.9800000000000000e+002,  7.3800000000000000e+002,  6.7900000000000000e+002, 
			 6.2500000000000000e+002,  5.7900000000000000e+002,  5.4300000000000000e+002, 
			 5.2100000000000000e+002,  5.1600000000000000e+002,  5.3100000000000000e+002, 
			-2.7370000000000000e+003]

## DRX FIR filter with decimation of 2
_drxFIR = [-6.2000000000000000e+001,  6.6000000000000000e+001,  1.4500000000000000e+002, 
			 3.4000000000000000e+001, -1.4400000000000000e+002, -5.9000000000000000e+001, 
			 1.9900000000000000e+002,  1.4500000000000000e+002, -2.2700000000000000e+002, 
			-2.5700000000000000e+002,  2.3200000000000000e+002,  4.0500000000000000e+002, 
			-1.9400000000000000e+002, -5.8300000000000000e+002,  9.2000000000000000e+001, 
			 7.8200000000000000e+002,  9.4000000000000000e+001, -9.9000000000000000e+002, 
			-3.9700000000000000e+002,  1.1860000000000000e+003,  8.5900000000000000e+002, 
			-1.3400000000000000e+003, -1.5650000000000000e+003,  1.3960000000000000e+003, 
			 2.7180000000000000e+003, -1.1870000000000000e+003, -4.9600000000000000e+003, 
			-1.8900000000000000e+002,  1.1431000000000000e+004,  1.7747000000000000e+004, 
			 1.1431000000000000e+004, -1.8900000000000000e+002, -4.9600000000000000e+003, 
			-1.1870000000000000e+003,  2.7180000000000000e+003,  1.3960000000000000e+003, 
			-1.5650000000000000e+003, -1.3400000000000000e+003,  8.5900000000000000e+002, 
			 1.1860000000000000e+003, -3.9700000000000000e+002, -9.9000000000000000e+002,
			 9.4000000000000000e+001,  7.8200000000000000e+002,  9.2000000000000000e+001,
			-5.8300000000000000e+002, -1.9400000000000000e+002,  4.0500000000000000e+002, 
			 2.3200000000000000e+002, -2.5700000000000000e+002, -2.2700000000000000e+002, 
			 1.4500000000000000e+002,  1.9900000000000000e+002, -5.9000000000000000e+001, 
			-1.4400000000000000e+002,  3.4000000000000000e+001,  1.4500000000000000e+002, 
			 6.6000000000000000e+001, -6.2000000000000000e+001]


_nPts = 1000 # Number of points to use in calculating the bandpasses


def freq2word(freq):
	"""
	Given a frequency in Hz, convert it to the closest DP tuning word.
	"""
	
	return int(round(freq*2**32 / fS))


def word2freq(word):
	"""
	Given a DP tuning word, convert it to a frequncy in Hz.
	"""
	
	return word*fS / 2**32


def delaytoDPD(delay):
	"""Given a delay in ns, convert it to a course and fine portion and into the 
	final format expected by DP (big endian 16.12 unsigned integer)."""
	
	# Convert the delay to a combination of FIFO delays (~5.1 ns) and 
	# FIR delays (~0.3 ns)
	sample = int(round(delay * fS * 16 / 1e9))
	course = sample // 16
	fine   = sample % 16
	
	# Combine into one value
	combined = (course << 4) | fine
	
	# Convert to big-endian
	combined = ((combined & 0xFF) << 8) | ((combined >> 8) & 0xFF)
	
	return combined


def DPDtodelay(combined):
	"""Given a delay value in the final format expect by DP, return the delay in ns."""
	
	# Convert to little-endian
	combined = ((combined & 0xFF) << 8) | ((combined >> 8) & 0xFF)
	
	# Split
	fine = combined & 15;
	course = (combined >> 4) & 4095
	
	# Convert to time
	delay = (course + fine/16.0) / fS
	delay *= 1e9
	
	return delay


def gaintoDPG(gain):
	"""Given a gain (between 0 and 1), convert it to a gain in the final form 
	expected by DP (big endian 16.1 signed integer)."""
	
	# Convert
	combined = int(32767*gain)
	
	# Convert to big-endian
	combined = ((combined & 0xFF) << 8) | ((combined >> 8) & 0xFF)
	
	return combined


def DPGtogain(combined):
	"""Given a gain value in the final format expected by DP, return the gain
	as a decimal value (0 to 1)."""
	
	# Convert to little-endian
	combined = ((combined & 0xFF) << 8) | ((combined >> 8) & 0xFF)
	
	# Convert back
	gain = combined / 32767.0
	
	return gain


def tbnFilter(sampleRate=1e5, nPts=_nPts):
	"""
	Return a function that will generate the shape of a TBN filter for a given sample
	rate.
	"""
	
	decimation = fS / sampleRate / 10
	decimationCIC = decimation / 2
	
	# CIC settings
	N =  2
	R = 98
	
	# Part 1 - CIC filter
	h = numpy.linspace(0, numpy.pi/decimationCIC/2, num=nPts, endpoint=True)
	wCIC = (numpy.sin(h*R)/numpy.sin(h/2))**N
	wCIC[0] = (2*R)**N
	
	# Part 2 - FIR filter
	h, wFIR = freqz(_tbnFIR, 1, nPts)
	
	# Cascade
	w = numpy.abs(wCIC) * numpy.abs(wFIR)
	
	# Convert to a "real" frequency and magnitude response
	h *= fS / decimation / numpy.pi
	w = numpy.abs(w)**2
	
	# Mirror
	h = numpy.concatenate([-h[::-1], h[1:]])
	w = numpy.concatenate([ w[::-1], w[1:]])
	
	# Return the interpolating function
	return interp1d(h, w/w.max(), kind='cubic', bounds_error=False)


def drxFilter(sampleRate=19.6e6, nPts=_nPts):
	"""
	Return a function that will generate the shape of a DRX filter for a given sample
	rate.
	
	Based on memo DRX0001.
	"""
	
	decimation = fS / sampleRate
	decimationCIC = decimation / 2
	
	# CIC settings
	N = 5
	R = 5
	     
	# Part 1 - CIC filter
	h = numpy.linspace(0, numpy.pi/decimationCIC/2, num=nPts, endpoint=True)
	wCIC = (numpy.sin(h*R)/numpy.sin(h/2))**N
	wCIC[0] = (2*R)**N
	
	# Part 2 - FIR filter
	h, wFIR = freqz(_drxFIR, 1, nPts)
	
	# Cascade
	w = numpy.abs(wCIC) * numpy.abs(wFIR)
	
	# Convert to a "real" frequency and magnitude response
	h *= fS / decimation / numpy.pi
	w = numpy.abs(w)**2
	
	# Mirror
	h = numpy.concatenate([-h[::-1], h[1:]])
	w = numpy.concatenate([w[::-1], w[1:]])
	
	# Return the interpolating function
	return interp1d(h, w/w.max(), kind='cubic', bounds_error=False)


def _processStreamBeam(data, intDelay, firFilter, gains, pol):
	"""
	Backend worker function for SoftwareDP for actually doing the beamforming.
	"""
	
	# Split out the gains
	XofX, XofY, YofX, YofY = gains
	
	# Delay
	## Integer
	temp = numpy.roll(data, intDelay)
	temp = temp.astype(numpy.float32)
	### FIR filter
	temp = lfilter(firFilter, 32767, temp)
	
	# Gain
	if pol is 0:
		## If the input is an X pol...
		contributionX = XofX*temp
		contributionY = XofY*temp
	else:
		## If the input is a Y pol...
		contributionX = YofX*temp
		contributionY = YofY*temp
		
	# Return
	return contributionX, contributionY


def _processStreamFilter(time, data, filterPack, centralFreq):
	"""
	Backend worker function for SoftwareDP for actually doing the DSP filtering.
	"""
	
	# Mix with the NCO
	temp = data*numpy.exp(-2j*numpy.pi*centralFreq*time/fS)
	temp -= temp.mean()

	# CIC filter + decimation
	temp = lfilter(filterPack['CIC'], 1, temp)[::filterPack['cicD']] / filterPack['cicD']
	
	# FIR filter + decimation
	temp = lfilter(filterPack['FIR'], 1, temp)[::filterPack['firD']]
	
	return temp


class SoftwareDP(object):
	"""
	Class to deal with processing TBW data after the fact like DP would.  This 
	provides a means to recreate any other DP output from a TBW capture for a 
	variety of purposes.  For example, a TBW file could be processed with the
	DRX filter 4 to create a data stream that can be correlated and imaged.
	
	.. note::
		Not all DP filters are supported by this class.  Supported filters are:
		  * TBN, filters 5, 6, and 7
		  * DRX, filters 3, 4, 5, 6, and 7
	
	.. versionchanged:: 0.5.2
		Added support for beamforming using the DP FIR coefficients and renamed 
		SoftwareDP.apply() to SoftwareDP.applyFilter().
	"""
	
	avaliableModes = {'TBN': {7: {'totalD': 1960, 'CIC': _tbnCIC7, 'cicD':  98, 'FIR': _tbnFIR, 'firD': 20},
						 6: {'totalD': 3920, 'CIC': _tbnCIC6, 'cicD': 196, 'FIR': _tbnFIR, 'firD': 20},
						 5: {'totalD': 7840, 'CIC': _tbnCIC5, 'cicD': 392, 'FIR': _tbnFIR, 'firD': 20},
						}, 
				   'DRX': {7: {'totalD':   10, 'CIC': _drxCIC7, 'cicD':   5, 'FIR': _drxFIR, 'firD':  2}, 
						 6: {'totalD':   20, 'CIC': _drxCIC6, 'cicD':  10, 'FIR': _drxFIR, 'firD':  2}, 
						 5: {'totalD':   40, 'CIC': _drxCIC5, 'cicD':  20, 'FIR': _drxFIR, 'firD':  2}, 
						 4: {'totalD':   98, 'CIC': _drxCIC4, 'cicD':  49, 'FIR': _drxFIR, 'firD':  2}, 
						 3: {'totalD':  196, 'CIC': _drxCIC3, 'cicD':  98, 'FIR': _drxFIR, 'firD':  2},
						},}
						
	delayFIRs = []
	for i in xrange(520):
		delayFIRs.append([])
		delayFIRs[-1].extend(_delayFIRs)
	
	def __init__(self, mode='DRX', filter=7, centralFreq=74e6):
		"""
		Setup DP for processing an input TBW signal.  Keywords accepted are:
		  * mode -> mode of operation (DRX or TBN)
		  * filter -> filter code for the given mode
		  * centralFreq -> tuning frequency for the output
		"""
		
		# Set the mode and make sure it is valid
		if mode not in self.avaliableModes:
			raise ValueError("Unknown mode '%s'" % mode)
		self.mode = mode
		
		# Set the filter and make sure it is valid
		filter = int(filter)
		if filter not in self.avaliableModes[self.mode]:
			raise ValueError("Unknown or unsupported filter for %s, '%i'" % (self.mode, filter))
		self.filter = filter
		
		# Set the tuning frequency and make sure it is valid
		centralFreq = float(centralFreq)
		if centralFreq < 10e6 or centralFreq > 88e6:
			raise ValueError("Central frequency of %.2f MHz outside the DP tuning range." % (centralFreq/1e6,))
		self.centralFreq = centralFreq
		
	def __str__(self):
		return "Sofware DP: %s with filter %i at %.3f MHz" % (self.mode, self.filter, self.centralFreq/1e6)
		
	def setMode(self, mode):
		"""
		Set the mode of operation for the software DP instance.
		"""
		
		if mode not in self.avaliableModes:
			raise ValueError("Unknown mode '%s'" % mode)
		self.mode = mode
		
	def setFilter(self, filter):
		"""
		Set the filter code for the current mode.
		"""
		
		filter = int(filter)
		
		if filter not in self.avaliableModes[self.mode]:
			raise ValueError("Unknown or unsupported filter for %s, '%i'" % (self.mode, filter))
		self.filter = filter
		
	def setCentralFreq(self, centralFreq):
		"""
		Set the tuning frequency for the current setup.
		"""
		
		centralFreq = float(centralFreq)
		
		if centralFreq < 10e6 or centralFreq > 88e6:
			raise ValueError("Central frequency of %.2f MHz outside the DP tuning range." % (centralFreq/1e6,))
		self.centralFreq = centralFreq
		
	def setDelayFIRs(self, channel, coeffs):
		"""
		Set the delay FIR coefficients for a particular channel to the list of lists 
		provided (filter set by filter coefficients).  If channel is 0, the delay FIR 
		filters for all channels are set to the provided values.  If channel is -1, 
		the delay FIR filters for all channels are set to the DP default values.
		"""
		
		# Make sure we have a list of lists
		try:
			nCoeff = len(coeffs[0])
		except TypeError:
			raise ValueError("Expected a list of lists for the coefficients.")
		
		if channel == -1:
			self.delayFIRs = []
			for i in xrange(520):
				self.delayFIRs.append([])
				self.delayFIRs[-1].extend(_delayFIRs)
		
		if channel == 0:
			self.delayFIRs = []
			for i in xrange(520):
				self.delayFIRs.append([])
				self.delayFIRs[-1].extend(coeffs)
			
		else:
			self.delayFIRs[channel-1] = coeffs
			
	def formBeam(self, antennas, time, data, courseDelays=None, fineDelays=None, gains=None, DisablePool=False):
		"""
		Process a given batch of TBW data using the provided delay and gain information to
		form a beam.
		"""
		
		try:
			from multiprocessing import Pool, cpu_count
			
			# To get results pack from the pool, you need to keep up with the workers.  
			# In addition, we need to keep up with which workers goes with which 
			# baseline since the workers are called asynchronously.  Thus, we need a 
			# taskList array to hold tuples of baseline ('count') and workers.
			taskPool = Pool(processes=cpu_count())
			taskList = []

			usePool = True
			progress = False
		except ImportError:
			usePool = False
			
		# Turn off the thread pool if we are explicitly told not to use it.
		if DisablePool:
			usePool = False
		
		# Output arrays
		beamX = numpy.zeros(data.shape[1])
		beamY = numpy.zeros(data.shape[1])
		
		# Loop over inputs to form the beam
		toCut = 0
		for i in xrange(data.shape[0]):
			pol = antennas[i].pol
			channel = antennas[i].digitizer
			stand = channel/2 + channel%2
			
			intDelay = courseDelays[i]
			firFilter = self.delayFIRs[channel-1][fineDelays[i]]
			gain = gains[i/2]
			
			if sum(gain) == 0:
				continue
			
			if intDelay > toCut:
				toCut = intDelay
			
			if usePool:
				# Use the pool
				task = taskPool.apply_async(_processStreamBeam, args=(data[i,:], intDelay, firFilter, gain, pol))
				taskList.append((i,task))
			else:
				# The pool is closed
				contributionX, contributionY = _processStreamBeam(data[i,:], intDelay, firFilter, gain, pol)
				beamX += contributionX
				beamY += contributionY
				
		if usePool:
			taskPool.close()
			taskPool.join()

			# This is where he taskList list comes in handy.  We now know who did what
			# when we unpack the various results
			for i,task in taskList:
				contributionX, contributionY = task.get()
				beamX += contributionX
				beamY += contributionY
				
			# Destroy the taskPool
			del(taskPool)
			
		# Trim the beams based on the FIFO delays
		beamX = beamX[toCut:]
		beamY = beamY[toCut:]
			
		return beamX, beamY
		
	def applyFilter(self, time, data, DisablePool=False):
		"""
		Process a given batch of TBW data using the current mode of operation.  This 
		function requires both an array of times (int64 in fS since the UNIX epoch) 
		and data (1-D or 2-D).  If 2-D data are given, the first dimension should be 
		over inputs and the second over time.
		
		.. versionchanged:: 0.5.2
			Renamed SoftwareDP.apply() to SoftwareDP.applyFilter()
		"""
		
		if len(data.shape) == 1:
			# Single input
			output = _processStreamFilter(time, data, self.avaliableModes[self.mode][self.filter], self.centralFreq)
		else:
			try:
				from multiprocessing import Pool, cpu_count
				
				# To get results pack from the pool, you need to keep up with the workers.  
				# In addition, we need to keep up with which workers goes with which 
				# baseline since the workers are called asynchronously.  Thus, we need a 
				# taskList array to hold tuples of baseline ('count') and workers.
				taskPool = Pool(processes=cpu_count())
				taskList = []

				usePool = True
				progress = False
			except ImportError:
				usePool = False
				
			# Turn off the thread pool if we are explicitly told not to use it.
			if DisablePool:
				usePool = False
			
			# Multiple inputs - loop over all of them
			output = [None for i in xrange(data.shape[0])]
			
			for i in xrange(data.shape[0]):
				if usePool:
					# Use the pool
					task = taskPool.apply_async(_processStreamFilter, args=(time, data[i,:], self.avaliableModes[self.mode][self.filter], self.centralFreq))
					taskList.append((i,task))
				else:
					# The pool is closed
					output[i] = _processStreamFilter(time, data[i,:], self.avaliableModes[self.mode][self.filter], self.centralFreq)
					
			if usePool:
				taskPool.close()
				taskPool.join()

				# This is where he taskList list comes in handy.  We now know who did what
				# when we unpack the various results
				for i,task in taskList:
					output[i] = task.get()

				# Destroy the taskPool
				del(taskPool)
				
			output = numpy.array(output)
			
		return output