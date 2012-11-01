
from Bio.Blast import NCBIWWW


class blast_html:

    def __init__(self):
        self.sequence = ""

    def get_blast_page(self,sequence):
        
        result = NCBIWWW.qblast('blastp','nr',sequence,format_type="HTML")
        result = result.read()
        result = result.replace('''src="css/''','''src="http://www.ncbi.nlm.nih.gov/blast/css/''')
        result = result.replace('''href="/blast/''','''href="http://www.ncbi.nlm.nih.gov/blast/''')
        result = result.replace('''<script src="blastResult.js">''','''<script src="http://www.ncbi.nlm.nih.gov/blast/blastResult.js">''')
        result = result.replace('''href="css/''','''href="http://www.ncbi.nlm.nih.gov/blast/css/''')
        result = result.replace('''src="js/''','''src="http://www.ncbi.nlm.nih.gov/blast/js/''')
        result = result.replace('''Blast.cgi?''','''http://www.ncbi.nlm.nih.gov/blast/Blast.cgi?''')
        result = result.replace('''href="#"''','''href="http://www.ncbi.nlm.nih.gov/blast/Blast.cgi#"''')
        result = result.replace('''/blast/images/''','''http://www.ncbi.nlm.nih.gov/blast/images/''')
        result = result.replace('''src="images/''', '''src="http://www.ncbi.nlm.nih.gov/blast/images/''')

        return result
