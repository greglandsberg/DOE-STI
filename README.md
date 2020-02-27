# DOE-STI - v1.1
Python Script for the DOE STI automatic paper submission - designed for the LHC paper upload, but can be used for other accepted papers as well. The current requirement is that the paper text must be available from either the public arXiv.org depository, which covers the vast majority of the HEP/astro papers, or CERN CDS.

Tested with Safari and Firefox on Mac OS X 10.15; please, report any problems under other systems

Requirements:
  python3 installed
  
    To have python3 installed, check https://www.python.org/downloads/mac-osx/
  
  selenium WebDriver interface installed
  
    With python3 installed, this is very simple:
    
    pip3 install selenium
    
    You can also check the following Web page: https://medium.com/technowriter/install-selenium-on-mac-os-x-94c7a216aeb0
    
    You will also need to install Safari and/or Firefox drivers for the script to work:
    
    Safari: the driver is already part of your Mac OS X system. You just need to intialize it:
    
        Before recording Web UI tests in Safari, make sure you enable Remote Automation in the Safari browser.
        To allow remote automation in Safari, you must turn on WebDriver support:
        To enable the Develop menu in the Safari browser, click Safari > Preferences > Advanced tab. 
        Select the Show Develop Menu check box. The Develop menu appears in the menu bar.
        To enable Remote Automation click Develop > Allow Remote Automation in the menu bar.
        Authorize safaridriver to launch the webdriverd service that hosts the local web server. 
        To permit this, run /usr/bin/safaridriver once manually and complete the authentication prompt.
        
    Firefox: the GeckoDriver driver is available from the github: 
      https://github.com/mozilla/geckodriver/releases/tag/v0.26.0
      
    After installation, you need to move it to a directory in the PATH, e.g. /usr/local/bin/
      
    Note that you if you run Mac OS X Catalina (10.15) or higher, you will need to disable notarization 
    for the driver to work. This is done via:
    
    xattr -r -d com.apple.quarantine geckodriver

usage:
python3 DOE.py [--help] [-d doi] [-f doi_list_file] [-c [DOE.cfg]] [-b Safari|Firefox]

Here the [-d doi] is an option to run the script for a single doi or arXiv references. The system is flexible enough to discard irrelevant information; below are examples of the "doi" filed that all work fine:

arXiv:1909.04721 
doi:10.1103/PhysRevLett.122.132001
10.1007/JHEP03(2019)082.
10.1007/JHEP03(2019)026
arXiv:1912.01662 [hep-ex]
arXiv:1909.09193 [hep-ex].
  arXiv:1902.08276 [hep-ex].

Note that if running from the command script, you need to put quotation marks around the doi references that contain colons, parentheses, or slashes, and for all the arXiv references, as they must contain "arXiv:" as a part of the name.

[-f doi_list_file]

With the -f option, you could provide a file with the references int he aove format; you could mix and match arXiv and doi entries, and you don't need quotes around them.

The code is driven by the DOE.cfg file, which you should edit with your own information. If you dont specify the -c option, the default DOE.cfg file is used; alternatively you could supply any other file in the same format.

Most of the fields are self-descriptive. You can use either single- or double-quotes, as the config file inluded with the distribution shows. The only tricky ones are the last two:

office = 'SC-25'        # This is a label from the DOE Sponsoring Office dropdown menu - SC-25 High-Energy Physics
category = '72'         # This is the category [72 - PHYSICS OF ELEMENTARY PARTICLES AND FILEDS

They are currently set for the papers in particle physics. If you want to set them up for some other fields, you should go to the submission form:

https://www.osti.gov/elink/2413-submission.jsp

follow it with some real or dummy information up to page 4 ("Content") and see which of the lines from the two drop-down menus: "Sponsoring DOE Program Office" and "Subject Categories" applies to your papers (I believe the SC-25 is still OK, but you should consider "79 ASTRONOMY AND ASTROPHYSICS" for the Subject Categories.

For every sibmitted paper, the system creates a file [doi].html in the directory where you run the script, which is a receipt of the submission. If a submission fails, you could look at this file to understand why. If it is successful, the file acts as a receipt. The [doi] in the file name is the actual doi reference, with the slashes replaced with periods.

If you have any problems with the usage, please report them to me at landsberg@hep.brown.edu.

Please, don't abuse the system with irrelevant uploads.

Happy uploading!

Greg
