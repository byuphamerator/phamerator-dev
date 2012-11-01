import cherrypy
import SOAPpy
import re
import random
from blast_html import *
server = SOAPpy.SOAPProxy("hatfull12.bio.pitt.edu:31415/")

###########################################################


class orderedList:

###########################################################
    
    def __init__(self,items):
        self.myList = []
        for item in items:
            self.myList.append(Node(item))
        self.myList.sort()
    def get_list(self):
        returnList = []
        for item in self.myList:
            returnList.append(item.item)
        
        return returnList
   
###########################################################     

class Node:
    def __init__(self,item):
        self.item = item
    def __cmp__(self,other):
        
        if type(self.item) == str:
            this = int(self.item)
            other = int(other.item)
            if this>other:
                return 1
            if this<other:
                return -1
            else:
                return 0 
        if type(self.item) == tuple:
        
            this = self.item[0]
            other = other.item[0]
    
            if this.rfind("gp")!= -1 and other.rfind("gp")!= -1:
    
                thisTuple = this.split("gp")
                otherTuple = other.split("gp")
                                
                thisFirst = thisTuple[0]
                otherFirst = otherTuple[0]

      
                try: thisLast = float(thisTuple[1].replace(")",""))
                except: thisLast = thisTuple[1].replace(")","")
                try: otherLast = float(otherTuple[1].replace(")",""))
                except: otherLast = otherTuple[1].replace(")","")

    
                if thisFirst<otherFirst:
                    return -1
                elif thisFirst>otherFirst:
                    return 1
                elif thisLast==otherLast:
                    return 0
                elif thisLast<otherLast:
                    return -1
                elif thisLast>otherLast:
                    return 1
            else:
                if this>other:
                    return 1
                if this<other:
                    return -1
                else:
                    return 0 
        






class webPham:

###########################################################
    
    head = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd"><html><head>
                <style type="text/css">
                    

                    /* 
	Theme Name: Pool
	Theme URI: http://www.lamateporunyogur.net/pool
	Description: A two columns blue theme for the best CMS, WordPress.
	Author: Borja Fernandez
	Author URI: http://www.lamateporunyogur.net
	Version: 1.0.7
		
	The CSS, XHTML and design is released under GPL:
	http://www.opensource.org/licenses/gpl-license.php
	
	
	Changelog:
		v1.0
			First Release
		v1.0.1
			Fixed search bug position
		v1.0.2
			Fixed search bug
			Added links.php
			Changed archives.php
		v1.0.3
			Remove cursor: pointer; from header
		v1.0.4
			Bug report from Nilson Cain fixed
			Class image center fixed
			Search form moved from header
			Changelog are now in style.css. Changelog.txt removed.
			Added logo with .psd file
			Other changes in css
		v1.0.5
			Move comments in index
			Other changes in css
		v1.0.6
			Changed sidebar
		v1.0.7
			Fixed rss feed and trackack uri if comments are closed (Thanks soteke)
*/

body {
	background: url(http://hatfull12.bio.pitt.edu:80/static/css/pool/images/bg.gif);
	color: #333;
	font-family: "Trebuchet MS", "Bitstream Vera Serif", Utopia, "Times New Roman", times, serif;
	margin: 0;
	padding-top: 31px;
	}

/* Structure Divs */
#content {
	background: #fff;
	border: 1px solid #9C9C9C;
	margin: 0 auto;
	padding: 5px;
	/*width: 795px;*/
	}

#header {
	background: #8EBAFD url(http://hatfull12.bio.pitt.edu:80/static/css/pool/images/logo.gif) no-repeat;
	height: 150px;
	margin: 0;
	padding: 0;
	}


#headerimg {
    margin: 0;
    height: 200px;
    width: 100%;
}

.narrowcolumn {
    float: left;
    padding: 0 0 20px 45px;
    margin: 0px 0 0;
    width: 555px; 
}

.widecolumn {
    padding: 10px 0 20px 0;
    margin: 5px 0 0 150px;
    width: 450px;
}

.post {
    margin: 0 0 4px;
    text-align: justify;
}

.widecolumn .post {
    margin: 0;
}

.narrowcolumn .postmetadata {
    padding-top: 5px;
}

.widecolumn .postmetadata {
    margin: 30px 0;
}

.widecolumn .smallattachment {
    text-align: center;
    float: left;
    width: 128px;
    margin: 5px 5px 5px 0px;
}

.widecolumn .attachment {
    text-align: center;
    margin: 5px 0px;
}

.postmetadata {
    clear: left;
}

#footer {
    padding: 0 0 0 1px;
    margin: 0 auto;
    width: 760px;
    clear: both;
}

#footer p {
    margin: 0;
    padding: 20px 0;
    text-align: center;
}
/* End Structure */



/*	Begin Headers */
h1 {
    padding-top: 15px;
    padding-bottom: 5px;
    margin: 0;
}

.description {
    text-align: center;
}

h2 {
    margin: 30px 0 0;
}

h2.pagetitle {
    margin-top: 30px;
    text-align: center;
}

#sidebar h2 {
    margin: 5px 0 0;
    padding: 0;
}

h3 {
    padding: 0;
    margin: 30px 0 0;
}

h3.comments {
    padding: 0;
    margin: 40px auto 20px ;
}
/* End Headers */



/* Begin Images */
p img {
    padding: 0;
    max-width: 100%;
}

/*	Using 'class="alignright"' on an image will (who would've
thought?!) align the image to the right. And using 'class="centered',
will of course center the image. This is much better than using
align="center", being much more futureproof (and valid) */

img.centered {
    display: block;
    margin-left: auto;
    margin-right: auto;
}

img.alignright {
    padding: 4px;
    margin: 0 0 2px 7px;
    display: inline;
}

img.alignleft {
    padding: 4px;
    margin: 0 7px 2px 0;
    display: inline;
}

.alignright {
    float: right;
}

.alignleft {
    float: left
}
/* End Images */

#nav {
margin: 0 auto;
padding: 0;
top: 0px;
right: 0px;
/*padding: 3px;*/
font-size: 14pt;
}

.navitem, li.navitem {
border: 1px solid gray;
display:inline;
list-style-type: none;
color: white;
background: goldenrod;
}

a.navitem, a.selected_navitem {
border: 0px;
padding-left: 5px;
padding-right: 5px;

}

li.navitem:hover{
blackground:black;
}

.selected_navitem{
display:inline;
list-style-type: none;
/*padding-left: 5px;
padding-right: 5px;*/
color: #0090DA;
border: 1px solid gray;
background: blanchedalmond;
}

li.selected_navitem{
color: #0090DA;
/*border-top: 1px solid black;
border-left: 1px solid black;
border-right: 1px solid black; */
}

a.navitem:hover, .navitem:hover {
display:inline;
color: white;
/*border: 1px dashed black;*/
background: #0090DA;
}


#pages {
	background: #B8D4FF;
	font-size: 12px;
	margin: 0;
	padding: 15px 0 6px 20px;
	}

#page {
    background-color: #B8D4FF;
    margin: 0 auto;
    padding: 0;
    width: 760px;
    border: 1px solid #959596;
}

.post {
    margin: 0 0 40px;
    text-align: justify;
}

	
#searchform {
	float: right;
	margin: 0;
	padding: 0;
	position: relative;
	right: 10px;
	top: 0px;
	/*top: -22px;*/
}	
	
#noticias {
	float: left;
	margin: 0;
	padding: 0 0 20px 20px;
	width: 550px;
	}

#sidebar {
	float: right;
	font-size: 11px;
	line-height: 1.5em;
	margin: 0;
	padding: 0 10px;
	width: 170px;
	}

#credits {
	background: #D5E5FE;
	font-family: Small Fonts, VT100, Arial, Helvetica;
	font-size: 9px;
	margin: 0;
	padding: 5px 20px;
	text-align: center;
	text-transform: uppercase;
	}

	
/* Config Structure Divs */

	/* Header */
	#header h1 {
		font-size: 26px;
		letter-spacing: 0.1em;
		margin: 0;
		padding: 20px 0 20px 30px;
		width: 300px;
		}
		
	#header a, #header a:hover {
		background: transparent;
		color: #fff;
		text-decoration: none;
		}
	
	/* Pages */
	#pages li {
		display: inline;
		list-style-type: none;
		}
		
	#pages ul, ol {
		margin: 0;
		padding: 0;
		}
		
	#pages a {
		background: #fff;
		color: #1E4C62;
		font-weight: bold;
		margin: 0 3px 0 0;
		padding: 6px 10px;
		}
		
	#pages a:hover {
		background: #8EBAFD;
		color: #fff;
		}
		
	.current_page_item a, .current_page_item a:hover {
		background: #8EBAFD !important;
		color: #fff !important;
		}
		
	/* Search */
	#searchform input {
		border: 1px solid #66A8CC;
		font-size: 12px;
		padding: 2px;
		width: 160px;
		}
			
	/* Noticias */
	#noticias p, #noticias ul, #noticias ol {
		font-size: 13px;
		line-height: 1.6em;
		}
			
	#noticias ul {
		list-style-type: circle;
		margin: 0 0 0 30px;
		padding: 0;
		}
			
	#noticias li {
		margin: 0;
		padding: 0;
		}

	#noticias h2, #noticias h2 a {
		color: #0090DA;
		font-size: 18px;
		font-weight: normal;
		margin: 50px 0 0 0;
		padding: 0;
		text-decoration: none;
		}
		
	#noticias h2 a:hover {
		background: transparent;
		color: #6EB9E0;
		}
		
	#noticias h3 {
		color: #016CA3;
		font-size: 15px;
		font-weight: normal;
		margin: 0;
		padding: 20px 0 5px 0;
		}

	#noticias small {
		font-family: Arial, Helvetica, Sans-Serif;
		font-size: 11px;
		}
		
	.feedback {
		color: #898A8A;
		font-size: 12px;
		margin: 0;
		padding: 0 20px;
		text-align: center;
		}
		
	/* Entrada */
	.entrada {
		margin: 0;
		padding: 0;
		}

	/* Comments */
	#commentlist {
		list-style-type: none;
		margin: 0;
		padding: 0;
		}

	#commentlist li {
		margin: 10px 0;
		padding: 5px 10px;
		}
			
	#commentlist p {
		margin: 0;
		padding: 0;
		}
			
	#commentlist small {
		font-size: 11px;
		}

	.class_comment1 { background: #E9E9EA; border: 1px solid #E0DEDE; }
	.class_comment2 { background: #F4F3F3; border: 1px solid #E0DEDE; }
	
	#comments, #postcomment {
		color: #0090DA;
		font-size: 14px !important;
		font-weight: normal;
		margin: 40px 0 10px 10px;
		text-transform: uppercase;
		}
			
	#commentform {
		background: #D3E4FF;
		border: 1px solid #D8D8D8;
		padding: 5px 20px;
		}
		
	#commentform input, #commentform textarea {
		background: #F9FBFF;
		border: 1px solid #B8D4FF;
		font-size: 12px;
		padding: 1px;
                width: 100%;
		}
		
	#commentform input:focus, #commentform textarea:focus {
		background: #EEF5FF;
		}
	#commentform #submit {
		margin: 0;
                width: 30%;
		}
	/* Sidebar */
	#sidebar h3 {
		background: url(http://hatfull12.bio.pitt.edu:80/static/css/pool/images/dot.gif) repeat-x bottom;
		color: #174B65;
		font-size: 11px;
		font-weight: normal;
		letter-spacing: 0.2em;
		margin: 0;
		padding: 0;
		text-transform: uppercase;
		}
		
	#sidebar ul, #sidebar ol {
		list-style: square;
		margin: 0;
		padding: 5px;
		}
		
	#sidebar li, #sidebar li:hover {
                /*border: 1px dashed;*/
		margin: 0;
		padding: 0;
		}
		
	#sidebar a {
		color: #0B76AE;
		}
		
	#sidebar a:hover {
		background: url(http://hatfull12.bio.pitt.edu:80/static/css/pool/images/dot.gif) repeat-x bottom;
		color: #0B76AE;
		}
		
	#sidebar div { 
		margin: 20px 0;
		padding: 0;
		}

	/*	Credits */
	#credits a {
		color: #3E708A;
		}
		
	#credits a:hover {
		background: transparent;
		color: #0090DA;
		}
		
	#credits p {
		margin: 0;
		padding: 0;
		}

/* General */
a {
	color: #0B76AE;
	text-decoration: none;
	}

a:hover {
	background: #0090DA;
	color: #fff;
	}

acronym, abbr, span.caps {
	cursor: help;
	border-bottom: 1px dotted #000;
	}
	
blockquote {
	background: #E3F5FE url(http://hatfull12.bio.pitt.edu:80/static/css/pool/images/blockquote.png) no-repeat bottom left;
	padding: 5px 20px 30px 20px;
	margin: 1em;
	} /* Idea from ShadedGrey of http://wpthemes.info/ */

cite {
	text-decoration: none;
	}
	
code {
	font-family: 'Courier New', Courier, Fixed, sans-serif;
	font-size: 1.1em;
	}

img {
	border: 0;
	}

h4 {
	color: #858585;
	}
	
/* Float and Clear */
div.floatleft {
	float: left;
	}

div.floatright {
	float: right;
	}
	
div.both {
	clear: both;
	}
	
/* Images align */
img.border {
	border: 1px solid #C6C6C6;
	padding: 4px;
	margin: 0;
	}

img.border:hover {
	background: #E3F5FE;
	}

img.center {
	display: block; 
	margin: auto;   
	}

img.alignright {
	float: right;
	padding: 4px;
	margin: 0 0 2px 7px;
	display: inline;
	}

img.alignleft {
	float: left;
	padding: 4px;
	margin: 0 7px 2px 0;
	display: inline;
	}
	
/* Text align */
.center {
	text-align: center;
	}
	
.alignright {
	text-align: right;
	}

.alignleft {
	text-align: left;
	}

/* from here to bottom was pasted from default style.css */

    .navigation {
        display: block;
        text-align: center;
        margin-top: 10px;
        margin-bottom: 60px;
    }
    /* End Various Tags & Classes*/

        #wpcombar {
            position: absolute;
            top: 0;
            left: 0;
            background: #14568a;
            width: 100%;
            height: 30px;
            font-family: "Lucida Grande", "Lucida Sans Unicode", Tahoma, Verdana;
            font-size: 12px;
        }

        #quicklinks ul {
            list-style: none;
            margin: 0;
            padding: 0;
        }

        #quicklinks li {
            float: left;
        }

        #quicklinks a {
            display: block;
            padding: .5em 1em;
            color: #c3def1;
            text-decoration: none;
            font-weight: normal;
        }

        #quicklinks a:hover {
            background: #6da6d1;
            color: black;
        }

        #loginout {
            position: absolute;
            right: 1em;
            top: 7px;
            margin: 0;
            padding: 0;
            color: #c3def1;
        }

        #loginout strong {
            color: #c3def1;
        }

        #loginout a, #loginout a:hover {
            color: white;
        }
        #statusmessage {
            position: absolute;
            top: -1px;
            left:200px;
            right: 200px;
            z-index: 5000;
        }

        #statusmessage div {
            width: 400px;
            margin: 0px auto;
            height: 50px;
            padding: 35px 10px 10px 55px;
            background-repeat: no-repeat;
            background-position: left;
            font-size: 18px;
            opacity: .75;
            filter: alpha(opacity=75);
        }
        #statusmessage div.success {
            background-color: #99CC99;
            border: 1px solid #006633;
            background-image: url("http://hatfull12.bio.pitt.edu:80/static/images/dialog-information.png");
        }

        #statusmessage div.error {
            background-color: #C00;
            border: 1px solid #600;
            background-image: url("http://hatfull12.bio.pitt.edu:80/static/images/dialog-error.png");
        }



        .btn {  background-color: transparent; border: 0; padding: 0;
		color: #1E4C62;
		font-weight: bold;
		margin: 0 3px 0 0;
		padding: 6px 10px;}


        .sectionBorder {
            border: 2px dashed #1E4C62;
            margin: 5%;
            padding: 5%;
            text-align: left;
        }
        .sectionOuterBorder {
            border: 1px solid grey;
            text-align: center;
            margin: 5%;
            padding: 5%;
        }
                </style>
                <title>The Phameration Station</title>
               </head>"""

###########################################################


    sidebar =  ( """
        <script type="text/javascript">
        function getVar(name)
         {
         get_string = document.location.search;         
         return_value = '';
         
         do { //This loop is made to catch all instances of any get variable.
            name_index = get_string.indexOf(name + '=');
            
            if(name_index != -1)
              {
              get_string = get_string.substr(name_index + name.length + 1, get_string.length - name_index);
              
              end_of_value = get_string.indexOf('&');
              if(end_of_value != -1)                
                value = get_string.substr(0, end_of_value);                
              else                
                value = get_string;                
                
              if(return_value == '' || value == '')
                 return_value += value;
              else
                 return_value += ', ' + value;
              }
            } while(name_index != -1)
            
         //Restores all the blank spaces.
         space = return_value.indexOf('+');
         while(space != -1)
              { 
              return_value = return_value.substr(0, space) + ' ' + 
              return_value.substr(space + 1, return_value.length);
							 
              space = return_value.indexOf('+');
              }
          
         return(return_value);        
         }
        </script>
        
        <script type="text/javascript">
            function update_size_n_adj(){
                try{
                    var past_trans = getVar("transparency");
        
                    var past_size = getVar("size");
        
                    //alert(past_trans + ":" + past_size);

                    if (past_trans == "ON"){

                        document.getElementById("adjustment_on").checked = true
                    }
                    else{
                        
                        document.getElementById("adjustment_off").checked = true

                    }
                    
                    if (past_size == "BIG"){
                        
                        document.getElementById("size_big").checked = true
                    }
            
                    else if (past_size == "MID"){
                        
                        document.getElementById("size_mid").checked = true
                    }
                    
                    else{
                
                        document.getElementById("size_sml").checked = true
                    }
                }
                catch(e){alert(e);}
            }
        </script>
        <script type="text/javascript">
        function get_size_n_adj(action,id,target){
        var form=document.getElementById(id);
        form.action = action;
        if (target == 'none'){
            form.target = "";
        }
        else{
            form.target = target;
        }
        var adjustment=document.getElementsByName("adjustment");
        var size = document.getElementsByName("size");
        for (i=0;i<adjustment.length;i++){
            if (adjustment[i].checked == true){
                var retAdj = adjustment[i].value;
            }
        }

        for (i=0;i<size.length;i++){
            if (size[i].checked == true){
                var retSize = size[i].value;
            }
        }
        try{
        document.getElementById("pham_input_trans").value=retAdj;
        }
        catch(e){}
        try{
        document.getElementById("pham_input_size").value=retSize;
        }
        catch(e){}
        try{
        document.getElementById("multiple_genome_input_trans").value=retAdj;
        }
        catch(e){}
        try{
        document.getElementById("multiple_genome_input_size").value=retSize;
        }
        catch(e){}
        try{
        document.getElementById("genome_input_trans").value=retAdj;
        }
        catch(e){}
        try{
        document.getElementById("genome_input_size").value=retSize;
        }
        catch(e){}
        try{
        document.getElementById("list_trans").value=retAdj;
        }
        catch(e){}
        try{
        document.getElementById("list_size").value=retSize;
        }
        catch(e){}
        form.submit();
        }
        </script>""" + 

        '''<div id="sidebar">''' + 
        """
        <h3>Transparency</h3>
        <br/>        
        <FORM id="select_adjustment" action = "">
        On:
        <input type="radio"
        name="adjustment" id="adjustment_on" value="ON"/>
        <br/>
        Off:
        <input type="radio" checked="checked"
        name="adjustment" id="adjustment_off" value="OFF"/>
        <br/>
        </FORM>""" +
        
        "<br/>" + 

        """
        <h3>PhamCircle Size</h3>
        <br/> 
        <FORM id="select_size" action="">        
        Small: 
        <input type="radio" checked="checked"
        name="size" id="size_sml" value="SML"/>
        <br/>
        Medium: 
        <input type="radio"
        name="size" id="size_mid" value="MID"/>
        <br/>
        Large:
        <input type="radio"
        name="size" id="size_big" value="BIG"/>
        <br/>
        </FORM>""" +
        "</div>")


###########################################################


    body = """<body onLoad="update_size_n_adj();"><div id="page"><div id="header"><h1><a href="http://hatfull12.bio.pitt.edu:80/">PhageHunter Program</a></h1></div>"""

###########################################################

    foot = """<div id="footer"><p><a>Phameration Station version 1.0</a></p></div></div></body></html>"""

###########################################################

    linkbar =  """<ul id="nav">
        <li class="navitem"><a href="http://hatfull12.bio.pitt.edu" class="navitem">Blog</a></li>

        <li class="navitem"><a href="http://hatfull12.bio.pitt.edu/wiki" class="navitem">Wiki</a></li>
        <li class="selected_navitem"><a href="/" class="selected_navitem">Phamerator</a></li>
        <li class="navitem"><a href="http://hatfull12.bio.pitt.edu/PhageHuntingWorkshop2007/calendar.html" class="navitem">Calendar</a></li>
    </ul>"""

###########################################################

    java = """
        <script type="text/javascript">
        function check_uncheck_all(){
        var box = document.getElementsByName("box");
        var boxList=document.getElementsByName("checked");
        var bool = box[0].checked;
            for (i=0;i<boxList.length;i++){
                boxList[i].checked = bool; 
            }
        }
        function get_action(button){
            var form=document.getElementById("choose_seq")
            var boxList=document.getElementsByName("checked");
            var numChecked = 0;
            for (i=0;i<boxList.length;i++){
                if (boxList[i].checked == true){
                    numChecked++;
                }
            }
            if (button == "blast"){
                
                if(numChecked > 1){
                    var r=confirm("Realise you are attempting to blast multiple sequences(this may take a while).  Many pop-up windows may ensue (make sure your browser is set to accept pop-ups from this site).  Do you want to continue?");        if(r == true){
                        form.action = "blast_page";
                        form.submit();
                    }
                }
                else{
                    form.action = "blast_page";
                    form.submit();
                }
            }
            else{
                form.action = "get_fasta";
                form.submit();
            }
        
        }
        </script>"""
###########################################################    

    def index(self):
        
        return  (self.head +  self.body + self.linkbar + self.sidebar +  
                
                '''<div id="content" class="narrowcolumn"> '''+ 
                    '''<div class="post" id="post-1">''' +
                        "<br/>" + self.pham_input() + 
                        "<br/>" + self.genome_input() + 
                        "<br/>" + self.multiple_genome_input() + 
                    "</div>" + 
                   "</div>" +
                 self.foot)
    index.exposed = True


###########################################################





    def circle(self,*args,**kw):
        pham = kw["pham"]
        trans = kw["transparency"]
        size = kw["circle_size"]
        if trans == "OFF":
            adjustment = 0.0
        else:
            adjustment = 1.0
        if size == "SML":
            radius = 150
        elif size == "MID":
            radius = 200
        else:
            radius = 300
        
        phams = []
        for item in server.get_unique_phams():
            item = str(item)
            phams.append(item)
        if pham not in phams:
            return "Pham " + pham + " Does Not Exist"
            
        server.create_pham_circle(pham,False,adjustment,radius)
        circle = server.get_phamCircle()
        #cherrypy.response.headers['Content-Type'] = 'application/xhtml+xml' 
        cherrypy.response.headers['Content-Type'] = 'image/svg+xml'
        return circle
    circle.exposed = True

###########################################################

    def genomeMap(self,*args,**kw):
        try:
            genome = kw["genome"]
        except:
            return "Please Select At Least One Genome..."
        if type(genome) == str:
            genome = [genome]              
        phageID = []  
        for gen in genome:
            ID = server.get_PhageID_from_name(gen)
            phageID.append({"PhageID":ID,"display_reversed":False})
        server.create_genome_map(phageID)
        genMap = server.get_genome_map()
        cherrypy.response.headers['Content-Type'] = 'image/svg+xml'
        return genMap
    genomeMap.exposed = True
    

###########################################################        
   

    def phamList(self,*args,**kw):
        genome = kw["genome"]
        phageID = server.get_PhageID_from_name(genome)
        phamList = orderedList(server.get_phams_from_PhageID(phageID)).get_list()
        head = """<h1>Phamilies for """ + genome + """</h1><ul>"""
        foot = """</ul>"""
        middle =  '''<form name="phamList" id="listPhams" action="circle" method="GET" target="_blank" >''' 
        for item in phamList:
            if server.get_number_of_pham_members(item) >= 2:
#<a href="''' + "/circle/?pham=" + item + '''">''' + item + """</a>
                middle = middle + '''<li><a>''' + '''<input type="submit" class="btn" onclick="get_size_n_adj('circle','listPhams','_blank')" name="pham" value="''' + item + '''">''' +"""</a></li>""" + "<br/>"
            else:
                middle = middle + '''<li>''' + item + """ (single member)</li>""" + "<br/>"

        middle = middle + """<input type="hidden" id="list_trans" name="transparency" value=""/><input type="hidden" id="list_size" name="circle_size" value=""/></form>"""

        return (self.head +  self.body + self.linkbar + self.sidebar +  '''<div id="content" class="narrowcolumn"> '''+ 
                    '''<div class="post" id="post-1">''' + head + middle + foot + """</div></div>""" + self.foot)
    phamList.exposed = True

###########################################################

 
  

    def geneList(self,*args,**kw):
        exp = re.compile('\d+[.]*\d*$')
        genome = kw["genome"]
        phageID = server.get_PhageID_from_name(genome)
        geneList = server.get_genes_from_PhageID(phageID)
        head = """<html><body><h1>Genes for """ + genome + """</h1><ul>"""
        foot = """</ul></body></html>"""
        middle = '''<form name="geneList" id="listGenes" action="circle" method="GET" target="_blank" >''' 
        tempList = []
        for item in geneList:
            tempList.append(("gp" + str((exp.search(server.get_gene_name_from_GeneID(item))).group().strip()),item))
        geneList = orderedList(tempList).get_list()
        for item in geneList:
            if server.get_number_of_pham_members(server.get_pham_from_GeneID(item[1])) >=2:
                middle = middle + '''<li>''' + item[0] + " Pham" + '''<a><input type="submit" class="btn" onclick="get_size_n_adj('circle','listGenes','_blank')" name="pham" value="''' + str(server.get_pham_from_GeneID(item[1])) + '''"></a>''' + """</li>""" + "<br>"
            else:
                middle = middle + '''<li>''' + item[0] + """ (single member pham)</li>""" + "<br/>"
        middle = middle + """<input type="hidden" id="list_trans" name="transparency" value=""/><input type="hidden" id="list_size" name="circle_size" value=""/></form>"""

        return (self.head +  self.body + self.linkbar + self.sidebar +  '''<div id="content" class="narrowcolumn"> '''+ 
                    '''<div class="post" id="post-1">''' + head + middle + foot + """</div></div>""" + self.foot)
    geneList.exposed = True

###########################################################


    def choose_seq_by_pham(self,*args,**kw):
        pham = kw["pham"]
        phams = []
        for item in server.get_unique_phams():
            item = str(item)
            phams.append(item)
        if pham not in phams:
            return "Pham " + pham + " Does Not Exist"
            pass
        
        
        head = """<html>""" + self.java + """<body><h1>Genes for Phamily """ + pham + """</h1><form id="choose_seq" action="" method="GET" target="_blank"><ul>"""
        foot = """</ul><input type="button" value="Get Fasta" onclick="get_action('fasta')" /><input type="checkBox" name="box" onclick="check_uncheck_all()"/><a>check/uncheck all</a><br/><input type="button" value="Blast" onclick="get_action('blast')" /></form></body></html>"""
        middle = ""
        members = server.get_members_of_pham(pham)
        for item in members:
            middle = middle + '''<li><input type="checkBox" name="checked" value="''' + item + '''"/><a>''' + server.get_phage_name_from_PhageID(server.get_PhageID_from_GeneID(item)) + " : " + server.get_gene_name_from_GeneID(item).replace(server.get_phage_name_from_GeneID(item),"") + '''</a></li>''' + "<br/>"
        return (self.head +  self.body + self.linkbar + self.sidebar +  '''<div id="content" class="narrowcolumn"> '''+ 
                    '''<div class="post" id="post-1">''' + head + middle + foot + """</div></div>""" + self.foot)
    choose_seq_by_pham.exposed = True

###########################################################

    


    def choose_seq_by_genome(self,*args,**kw):
        genome = kw["genome"]
        head = """<html>""" + self.java + """<body><h1>Genes for """ + genome + """</h1><form id="choose_seq" action="" method="GET" target="_blank"><ul>"""
        foot = """</ul><input type="button" value="Get Fasta" onclick="get_action('fasta')" /><input type="checkBox" name="box" onclick="check_uncheck_all()"/><a>check/uncheck all</a><br/><input type="button" value="Blast" onclick="get_action('blast')" /></form></body></html>"""
        middle = ""
        
        phageID = server.get_PhageID_from_name(genome)
        geneList = server.get_genes_from_PhageID(phageID)
        exp = re.compile('\d+[.]*\d*$')
        tempList = []
        for item in geneList:
            tempList.append(("gp" + str((exp.search(server.get_gene_name_from_GeneID(item)).group().strip())),item))
        geneList = orderedList(tempList).get_list()
        
        for item in geneList:
             middle = middle + '''<li><input type="checkBox" name="checked" value="''' + item[1] + '''"/><a href="''' + "/get_fasta/?checked=" + item[1] + '''">''' + item[0] + """</a></li>""" + "<br/>"
        return (self.head +  self.body + self.linkbar + self.sidebar +  '''<div id="content" class="narrowcolumn"> '''+ 
                    '''<div class="post" id="post-1">''' + head + middle + foot + """</div></div>""" + self.foot)
    choose_seq_by_genome.exposed = True


###########################################################


    def blast_page(self,*args,**kw):
        try:
            checked = kw["checked"]
            if type(checked) == str:
                title = "  " + server.get_phage_name_from_GeneID(checked) + "_" + server.get_gene_name_from_GeneID(checked).replace(server.get_phage_name_from_GeneID(checked),"") + "</title>"
                html = blast_html().get_blast_page(server.get_translation_from_GeneID(checked))
                html = html.replace('''</title>''',title)
                return html
            else:
                
                returnString = """<html><body onLoad="open_multiple();">
                <script type="text/javascript">
                    function open_multiple() {"""
                for item in checked:
                    returnString = returnString + '''window.open("/blast_page?checked=''' + item + '''");'''
                returnString = returnString + """window.close();}</script></body></html>"""
                return returnString
            
        except:
            return "Please Select at Least One Gene..."
    blast_page.exposed = True


###########################################################


    def get_fasta(self,*args,**kw):
        try:
            checked = kw["checked"]
        except:
            return "Please Select at Least One Gene..."
        returnString = ""
        if type(checked) == str:
            checked = [checked]
        for item in checked:
            returnString = returnString + '>' + server.get_phage_name_from_GeneID(item).replace('Mycobacterium phage', '').replace('Mycobacteriophage','') + '|' + server.get_gene_name_from_GeneID(item).replace(server.get_phage_name_from_GeneID(item),"") + '\n' + '<br/>'  + server.get_translation_from_GeneID(item) + '\n' + '<br/>'
        return returnString
    get_fasta.exposed = True



###########################################################

    def pham_input(self):
        return """<div class="sectionOuterBorder"><h2>Phamily Input</h2><div class="sectionBorder"><form name="pham_input" form id="phamInput" action="circle" method="GET" target="_blank">Pham:
                <input type="text" name="pham" /><br/>
                <input type="submit" value="Draw Pham Circle" onclick="get_size_n_adj('circle','phamInput','_blank')"/>
                <input type="button" value="Get/Blast Sequence" onclick="get_size_n_adj('choose_seq_by_pham','phamInput','none')"/>
                <input type="hidden" id="pham_input_trans" name="transparency" value=""/>
                <input type="hidden" id="pham_input_size" name="circle_size" value=""/>
                </form></div></div>"""
 
###########################################################

   
    def multiple_genome_input(self):
        head = """<div class="sectionOuterBorder"><h2>Multiple Genome Input</h2><div class="sectionBorder"><form action="genomeMap" method="GET" target="_blank"><select multiple size="20" name="genome">"""


        foot = """</select><input type="submit" value="Generate Map"/></form></div></div>"""

        phages = server.get_phages(name=True)
        middle = ""
        #try:
        #  phages.sort()
        for name in phages:
          middle = middle + "<option>" + name + "</option>"
        #except:
        #errMsg = "no phages were found in the database"
        #middle = "<option>%s</option>" % errMsg

        return head + middle + foot

###########################################################


    def genome_input(self):
        head = """<div class="sectionOuterBorder"><h2>Genome Input</h2><div class="sectionBorder"><form name="genome_input" id="genomeInput" action="" method="GET" ><select name="genome">"""


        foot = """</select><br/>
                <input type="button" value="List Phams" onclick="get_size_n_adj('phamList','genomeInput','none')"/>
                <input type="button" value="List Genes" onclick="get_size_n_adj('geneList','genomeInput','none')" />
                <input type="button" value="Get/Blast Sequence" onclick="get_size_n_adj('choose_seq_by_genome','genomeInput','none')"/>
                <input type="hidden" id="genome_input_trans" name="transparency" value=""/>
                <input type="hidden" id="genome_input_size" name="circle_size" value=""/>
        
        </form></div></div>"""

        phages = server.get_phages(name=True)
        middle = ""
        try:
          phages.sort()
          for name in phages:
            middle = middle + "<option>" + name + "</option>"
        except:
          errMsg = "no phages were found in the database"
          middle = "<option>%s</option>" % errMsg

        return head + middle + foot

###########################################################

cherrypy.root = webPham()
if __name__ == '__main__':
    cherrypy.config.update(file = 'web-pham.conf')
    cherrypy.server.start()




























