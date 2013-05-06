Phamerator
==========

Overview
--------
****
This is a fork being worked on by Brigham Young University and is NOT the 
official Phamerator repository.
****
Phamerator is a set of computer programs that is useful for genomic analysis
of bacteriophage genomes. In fact, these programs were specifically designed
for this purpose.

Phamerator is released under a free software license.  See LICENSE.txt for
more details.

Documentation for this project can be found in the doc directory.

(C) 2006-2008 Steve Cresawn <scresawn@gmail.com>
(C) 2006-2008 Matt Bogel <dabogsta@gmail.com>

Homepage: http://phage.cisat.jmu.edu

This project was forked under GNU License v2 section 2 as above.

Requirements
------------

For the server backend, you will need

* Python 2.7
* Biopython 1.42 or newer (python-biopython)
* Pyro 3.14 (pyro) (note that version 4.x does not work as it is for Python 3.x)
* ClustalW (clustalw) - this package is located in non-free for Debian distributions
* ClustalOmega (clustalo) - also non-free, only required if using phamClientOmega.py
* BLAST (ftp://ftp.ncbi.nih.gov/blast/executables/release/LATEST)
* Parallel Python (python-pp)
* MySQL for Python (python-mysqldb)
* curl
* MySQL Server (mysql-server)

In addition, for the GUI you will need

* Python GooCanvas Bindings (python-pygoocanvas)
* Python Webkit Bindings (python-webkit)
* Python Gnome configuration Bindings (python-gconf)
* GTK+ 3 or newer

Phamerator Quick-Start Guide
----------------------------------

These instructions are intended to get you up and running with Phamerator. For 
more complete documentation for each script, please see usage instructions, 
usually by running the script in question with no arguments. Before continuing 
with this guide, be sure to install all the required dependencies at the 
beginning of this document.

Downloading Phamerator
----------------------------------

This Phamerator repository uses a program called Git. In order to download it, 
it is recommended that you first install Git, in order to facilitate quick 
updates of the Phamerator program. To install Git on a Debian-based Linux 
system (including Ubuntu), run the command:

> sudo apt-get install git

After installing Git, you can download the latest version of this branch of 
Phamerator by running this command, which will download to the current working 
directory:

> git clone https://github.com/phamerator/phamerator-dev.git

After downloading Phamerator with Git, in order to check for updates, simply 
change into the new phamerator directory that was downloaded and then run:

> git pull

and Git will check for any updates that might have been made since you last 
downloaded files from the repository.

Setting Up the Database
----------------------------------

Before Phamerator can be used a database back-end must be set up to accept new 
phage records. Phamerator uses MySQL. We will set up a new database, and then 
write the Phamerator schema to that new database. Finally, we will grant 
permissions to a new user on that database.

First, let’s create the database. During installation of mysql-server you 
should have created a root password for your database through a prompt in the 
installer. Run this command and enter that root password when prompted:

> mysql -u root -p

If login is successful, you will be greeted with the MySQL prompt. At the 
prompt, run these commands to create a new database and grant access to a user 
for Phamerator:

> mysql> CREATE DATABASE $database$;

> mysql> GRANT SELECT, DROP, DELETE, INSERT, CREATE, LOCK TABLES, UPDATE on 
$database$.* to $username$ IDENTIFIED BY “$password$”;

> mysql> FLUSH PRIVILEGES;

Replace $database$ with the name of your new database, $username$ with the name 
of your new user, and $password$ with the password for your new user. 
$database$ should be the same in both commands. If no errors result, we can 
exit the command prompt:

> mysql> quit

To finish our database installation, we need to dump the database schema into 
our new database. The schema for Phamerator is included with the Phamerator 
files, in $phamerator-repo$/phamerator/sql/db_schema.sql, where 
$phamerator-repo$ is the name of the folder that you downloaded the Phamerator 
development snapshot repository. In order to install the schema, run this 
command on the command prompt:

> mysql -u root -p $database$ < $phamerator-repo$/phamerator/sql/db_schema.sql

$database$ is the name of the database you created earlier, and 
$phamerator-repo$ is the name of the Phamerator repository directory, as 
before. Note the “<” character, pointing at your database name. You will be 
prompted for your root database password. If there is no error, your database 
installation is complete!

Entering Data Into the Phamerator Database
----------------------------------

Phamerator data entry jobs typically take 5 steps:

1. Ensure compliance of GenBank files before database import
2. Add GenBank files to the database
3. Run genome alignments on sequences in the database using ClustalW and Blast
4. Build the Phams list and enter it into the database
5. Determine conserved domains using the NCBI Conserved Domain Database

Before any data entry can take place we must ensure that any GenBank files used 
are compliant with the format that Phamerator accepts. To do this, we will use 
the fix_dnaMaster_gb.py script, located in the phamerator/plugins directory. 
Collect your GenBank files into a directory and run the script on them like so:

> ./phamerator/plugins/fix_dnaMaster_gb.py /path/to/ImportSequences

where the first and only argument is a path to the directory containing your 
sequences you would like to import. The script will check the format of all 
GenBank files in that directory and write out a new version of each with a 
“.fixed” suffix.

Now we are ready to start importing GenBank files into the database. For this 
task we will use the phamerator_manage_db.py script, located in the phamerator 
directory. To import the GenBank files we checked in the previous step, run the 
command

> ./phamerator/phamerator_manage_db.py -u $username$ -p -s $database-server$ -d 
$database$ -i /path/to/ImportSequences

where $username$ is your database username, $database-server$ is the hostname 
of your database server, and $database$ is the name of your database.

Next it is time to run genome alignments on the newly added data. To do this, 
we will run the phamServer_InnoDB.py script, located in the phamerator 
directory. First, let’s run the server for ClustalW:

> ./phamerator/phamServer_InnoDB.py -u $username$ -p -s $database-server$ -n 
localhost -d $database$ -i 1 -l True -a clustalw

where $username$ is your database username, $database-server$ is the hostname 
of your database server, and $database$ is the name of your database. This will 
start an instance of the phamServer for ClustalW. In order to run any 
sequences, we will then have to connect to the server with a client. To do 
this, open another terminal, leaving the server running in your old one, and 
run:

> ./phamerator/phamClient.py -u $username$ -p -n localhost

If you would like to use the new Clustal Omega implementation, do

> ./phamerator/phamClientOmega.py -u $username$ -p -n localhost

where $username$ is your database username. This script will run alignments 
that the phamServer deals out.

In order to run blast jobs, repeat the previous server step, but with 
“blast” for the -a argument on the phamServer_InnoDB.py script. To run 
blast jobs, use the blastclient.py script, in the phamerator directory, like so:

> ./phamerator/blastclient.py -u $username$ -p -n localhost -a $path-to-blast$ -
d 
$path-to-blast-data$

where $username$ is your database username, $path-to-blast$ is the path to your 
Blast binaries, and $path-to-blast-data$ is your Blast datapath.

Depending on the amount of data to be processed, ClustalW and Blast jobs can 
take a very long time, so remember to be very patient!

Next we will build the Pham list and import it into the database. To do this, 
we use the phamBuilder4.py script in the phamerator directory. Values for the 
-c and -b options will depend on your analysis. They define the cutoff points 
that make a protein acceptable to join the Pham being built. Some sample values 
are provided  below. See the script usage for more information. Run the command 
like this:

> ./phamerator/phamBuilder4.py -u $username$ -p -s $database-server$ -d 
$database$ -c 0.325 -b 1e-50

where $username$ is your database username, $database-server$ is the hostname 
of your database server, and $database$ is the name of your database. This 
process also takes a long time, so now is a great time to take a break.

Finally, you have the option of determining conserved domains for the Phams in 
the database using the NCBI CDD database. For this to work, you will need to 
get a copy of the CDD database from NCBI 
(http://www.ncbi.nlm.nih.gov/Structure/cdd/cdd.shtml). To run a search, use the 
cddSearch.py script, located in the phamerator/plugins directory. For usage, please
run the script with no options.

Phamerator GUI
----------------------------------

The Phamerator GUI is easy to use. If you already have a database set up by 
following the instructions above, all you have to do is start the GUI by 
running ./phamerator/Phamerator on the command line. Before the GUI starts you 
will be prompted for your database information. After a successful login, the 
Phamerator GUI will appear.

The first time that you run the Phamerator GUI, it will create a configuration 
file for itself in your home folder, at ~/.phamerator/phamerator.conf. This 
file contains sensible defaults, but they will need to be changed you have 
extra databases you would like to connect to (otherdatabases) or if you would 
like to change your Blast directory (blast_dir). Currently, the prompts before 
the GUI start override the settings in the configuration file for the default 
database and default server. 

If you don’t have the required permissions on your database for the 
Phamerator GUI but you have the root password for your database, simply start 
Phamerator as above and enter your desired username and password. Phamerator 
will prompt you for your root password and attempt to add your username and 
password to the allowed list of users for the database.

One of Phamerator’s features is running local Blast jobs on entries in the 
database. In order to do that you will have to have a local copy of the Blast 
binaries on your machine. If Phamerator does not detect the required binaries 
on your machine on start it will download them for you into the directory 
specified by blast_dir in the configuration file.
