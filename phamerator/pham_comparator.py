import MySQLdb
import time
import random
#import threading
import db_conf
import sys

class pham_comparator:
    
    def compare_B_to_C(self, pB, pC):
        
             
        for b_pham in pB.phams:
                     
            for c_pham in pC.phams:

                match = 0                            

                for b_gene in pB.phams[b_pham]:
                    
                    for c_gene in pC.phams[c_pham]:
                        
                        if c_gene == b_gene:
                            
                            match += 1
                            
                            #print 'The gene ' + c_gene + ' is present in both phams'
                percentage = (match/len(pC.phams[c_pham]))*100
                if percentage != 0 and len(pC.phams[c_pham]) > 1 and len(pB.phams[b_pham]) > 1: print 'Blast pham ' + str(b_pham) + ' is ' + str(percentage) +'% similar to Clustal pham ' + str(c_pham)
                if percentage > 100: print pB.phams[b_pham], '\n', pC.phams[c_pham]
                
    
    
    def compare_C_to_B(self, pB, pC):
        
             
        for c_pham in pC.phams:
                     
            for b_pham in pB.phams:

                match = 0                            

                for c_gene in pC.phams[c_pham]:
                    
                    for b_gene in pB.phams[b_pham]:
                        
                        if b_gene == c_gene:
                            
                            match += 1
                            
                            #print 'The gene ' + c_gene + ' is present in both phams'
                percentage = (match/len(pB.phams[b_pham]))*100
                if percentage != 0 and len(pC.phams[c_pham]) > 1 and len(pB.phams[b_pham]) > 1: print 'Clustal pham ' + str(c_pham) + ' is ' + str(percentage) +'% similar to Blast pham ' + str(b_pham)
        
    
