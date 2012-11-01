import MySQLdb
import time
import random
#import threading
import db_conf
import sys

class pham_comparator:
    
    def compare(self, pB, pC, compare_type):
        
             
        for b_pham in pB.phams:
                     
            for c_pham in pC.phams:

                match = 0.                            

                for b_gene in pB.phams[b_pham]:
                    
                    for c_gene in pC.phams[c_pham]:
                        if c_gene == b_gene:
                            
                            match += 1.
                           # print 'The match number is now: ' + str(match)
                           # print 'The gene ' + c_gene + ' is present in both phams'
               # if match != 0:
		 	#print 'the match number is: ' + str(match)
                 	#print 'the length of the clustal pham is: ' + str(len(pC.phams[c_pham]))
		#percentage = (match/len(pC.phams[c_pham]))*100.0
                #if percentage == 100: 

			#print pB.phams[b_pham]
			#print '\n'
			#print '\n' 
			#print pC.phams[c_pham]
			#print len(pB.phams[b_pham])
		if match > 1:
			if compare_type == 'bc':
				print 'Blast pham ' + str(b_pham) + ' size: ' + str(len(pB.phams[b_pham])) + '   Clustal pham ' + str(c_pham) + ' size: ' + str(len(pC.phams[c_pham])) + '\nNumber of entries in the Blast pham which match the Clustal pham: ' + str(match)
                	elif compare_type == 'cb':
				print 'Clustal pham ' + str(b_pham) + ' size: ' + str(len(pB.phams[b_pham])) + '   Blast pham ' + str(c_pham) + ' size: ' + str(len(pC.phams[c_pham])) + '\nNumber of entries in the Clustal pham which match the Blast pham: ' + str(match)
 			elif compare_type == 'bb':
				print 'Blast pham ' + str(b_pham) + ' size: ' + str(len(pB.phams[b_pham])) + '   Blast pham ' + str(c_pham) + ' size: ' + str(len(pC.phams[c_pham])) + '\nNumber of entries in the Blast pham which match the Blast pham: ' + str(match)
    			else:
		     		print 'Clustal pham ' + str(b_pham) + ' size: ' + str(len(pB.phams[b_pham])) + '   Clustal pham ' + str(c_pham) + ' size: ' + str(len(pC.phams[c_pham])) + '\nNumber of entries in the Clustal pham which match the Clustal pham: ' + str(match)
