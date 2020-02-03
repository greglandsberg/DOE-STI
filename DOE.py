#!/usr/bin/env python
#
#   This script works with python3 and selenium Web interface; it requires the web browser driver
#   fo selenium and has been configured to work with either Safari or Firefox.
#   The script is designed to submit the Accepted Manuscript products to the DOE STI interface
#
#   Usage: python3 DOE.py [--help] [-d doi] [-f doi_list_file] [-c [DOE.cfg]] [-b Safari|Firefox]
#
#   (C) Greg Landsberg, 2020
#   E-mail: landsberg@hep.brown.edu
#
#   Version history:
#   v1.0 - 02-Feb-2020
#   v1.1 - 03-Feb-2020 - added a CDS interface for the articles that are in CERN CDS, but not on arXiv
#-------------------------------------------------------------------------------------
import ssl
import time
import codecs
import os
import sys
from os import path
import selenium
import urllib.request
from selenium import webdriver
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
#
def parseDOI(doi):  # parses either doi or arXiv reference
    value = {}
    value[0] = ''
    value[1] = ''
    value[2] = ''
    value[3] = ''
    value[4] = ''
    value[5] = ''
    value[6] = ''
    arXiv = ""
    journal = ""
    volume = ""
    year = ""
    page = ""
    DOI = ""
    ifarXiv = False
    doi = doi.strip(' .').lstrip(' ')
    doi = doi.replace(' ','')
    if doi == '' :
        return value
    if 'doi:' in doi or 'DOI:' in doi :
        doi = doi[doi.find(':')+1:len(doi)]
    if 'arXiv' in doi or 'arxiv' in doi :
        if ' ' in doi :
            doi = doi[doi.find(':')+1:doi.find(' ')]
        else :
            doi = doi[doi.find(':')+1:len(doi)]
        arXiv = 'arXiv:'+doi
        ifarXiv = True
    else :
        DOI = doi
    req = urllib.request.Request("http://inspirehep.net/search?ln=en&ln=en&of=hx&action_search=Search&sf=earliestdate&so=d&rm=&rg=25&sc=0&p="+doi)
    context = ssl._create_unverified_context()
    response = urllib.request.urlopen(req,context=context)
    INSPIREentry=response.read().decode("utf-8").splitlines()
    bibtex = False
    for line in INSPIREentry :
        if "@article" in line :    # Found a BiBTex block
            bibtex = True
        elif bibtex : # Analyzing the BiBTeX block
            payload = line[line.find('"')+1:line.rfind('"')]
            if "journal" in line : # found journal
                journal = payload
            elif "volume" in line : # found volume
                volume = payload
            elif "year" in line : # Found year
                year = payload
            elif "pages" in line :
                page = payload
            elif "doi" in line :
                if ifarXiv :
                    DOI = payload
            elif "eprint" in line :  # found an arXiv entry
                if not ifarXiv :
                    arXiv = payload
            elif "archivePrefix" in line :  # found an arXiv prefix
                if not ifarXiv :
                    arXiv = payload + ':' + arXiv
                break
            elif "reportNumber" in line :   # arXiv not found, but there is a preprint number
                value[6] = payload
    value[0] = arXiv
    value[1] = journal
    value[2] = volume
    value[3] = year
    value[4] = page
    value[5] = DOI
    return value
#---------------------------------
def getAbstractCDS(report):
    value = {}
    CDSURL =  "http://cds.cern.ch/search?ln=en&sc=1&action_search=Search&op1=a&m1=a&p1=&f1=&c=Articles+%26+Preprints&c=Books+%26+Proceedings&c=Presentations+%26+Talks&c=Periodicals+%26+Progress+Reports&c=Multimedia+%26+Outreach&p="+report
    req = urllib.request.Request(CDSURL)
    context = ssl._create_unverified_context()
    response = urllib.request.urlopen(req,context=context)
    page = response.read().decode("utf-8").splitlines()
    report = ""
    for line in page :
        if 'class="moreinfo">' in line :    # Found the CDS record number
            report = 'http://cds.cern.ch/' + line[line.find('<a href="')+9:line.find('?')]
            break
    req = urllib.request.Request(report)
    response = urllib.request.urlopen(req,context=context)
    page = response.read().decode("utf-8").splitlines()
    iline = 0
    for line in page :
        iline += 1
        if 'class="formatRecordLabel">' in line :    # Found the Abstract entry
            if 'Abstract' in page[iline] :
                abstract = page[iline+1][page[iline+1].find('">')+2:page[iline+1].find('</td></tr>')]
        elif 'class="detailedRecordActions">Fulltext:' in line : # Found the link to the PDF text
            report = 'http://cds.cern.ch/' + line[line.find('href=')+6:line.find('><img style')-1]
    value[0] = abstract
    value[1] = report
    return value

#---------------------------------------
def getAbstract(arXiv):
    arXivURL = "http://arxiv.org/abs/"+arXiv[arXiv.find(":")+1:len(arXiv)]
    req = urllib.request.Request(arXivURL)
    context = ssl._create_unverified_context()
    response = urllib.request.urlopen(req,context=context)
    page = response.read().decode("utf-8").splitlines()
    abstract = ""
    abs = False
    for line in page :
        if '<blockquote class="abstract mathjax">' in line :    # Found an abstract block
            abstract = line[line.find('</span>')+7:len(line)].lstrip(" ")
            abs = True
        elif abs and not '</blockquote>' in line :
            abstract += "\n" + line
        elif abs :
            break
    return abstract
#---------------------------------------
def getInfoFromArXiv(invalue):
    arXiv = invalue[0]
    journal= invalue[1]
    volume = invalue[2]
    year = invalue[3]
    page = invalue[4]
    DOI = invalue[5]
    value = invalue
    arXivURL = "https://arxiv.org/abs/"+arXiv[arXiv.find(":")+1:len(arXiv)]
    req = urllib.request.Request(arXivURL)
    context = ssl._create_unverified_context()
    response = urllib.request.urlopen(req,context=context)
    webpage = response.read().decode("utf-8").splitlines()
    abstract = ""
    injref = ""
    abs = False
    iline = 0
    for line in webpage :
        iline += 1
        if 'name="citation_doi"' in line and 'content="' in line:    # Found a doi reference
            DOI = line[line.find('content="')+9:len(line)-3]
        elif 'tablecell label' in line and 'Journal' in line: # found a journal info
            nextline = webpage[iline]
            if 'tablecell jref' in nextline : # found a journal info
                injref = nextline[nextline.find(">")+1:nextline.find("</td>")]
                if 'Phys. Rev.' in injref :
                    year = injref[injref.find("(")+1:injref.find(")")]
                    page = injref[injref.rfind(",")+1:len(injref)].lstrip(" ")
                    page = page[0:page.find(" ")]
                    injref = injref[0:injref.find(",")]
                    volume = injref[injref.rfind(" ")+1:len(injref)]
                    journal = injref[0:injref.find(volume)-1].rstrip(" ");
                else :
                    page = injref[injref.rfind(" ")+1:len(injref)]
                    year = injref[injref.find("(")+1:injref.find(")")]
                    journal = injref[0:injref.find("(")-1].rstrip(" ")
                    volume = journal[journal.rfind(" ")+1:len(journal)]
                    journal = journal[0:journal.find(volume)-1].rstrip(" ");
        elif '<blockquote class="abstract mathjax">' in line :    # Found an abstract block
            abstract = line[line.find('</span>')+7:len(line)].lstrip(" ")
            abs = True
        elif abs and not '</blockquote>' in line :
            abstract += "\n" + line
    value[0] = arXiv
    if value[1] == "" :
        value[1] = journal
    if value[2] == "" :
        value[2] = volume
    if value[3] == "" :
        value[3] = year
    if value[4] == "" :
        value[4] = page
    if value[5] == "" :
        value[5] = DOI
    value[6] = abstract
    return value
#--------------------------------------------
institution = 'Brown University'
url = 'https://www.osti.gov/elink/2413-submission.jsp'
grantID = 'SC0010010'
name = "Greg Landsberg, Thomas J. Watson, Sr. Professor of Physics"
email = "landsberg@hep.brown.edu"
phone = "(401) 863-1464"
office = 'SC-25'
category = '72'
cfgfile = 'DOE.cfg'
Safari = True
list = ""
doi = ''
failarXiv =[]
failDOI = []
failOther = []
CDS = {}
nSuccess = 0
nTotal = 0
#------------------------------------ Parsing input arguments
if len(sys.argv) > 1 :
    iline = 0
    for line in sys.argv :
        iline += 1
        if "--help" in line :
            print("Usage: python3 ",sys.argv[0]," -d DOI [--help] [-b Safari|Firefox")
            exit()
        elif "-d" in line :
            doi = sys.argv[iline]
        elif "-f" in line :
            file = sys.argv[iline]
            if not path.exists(file) :
                print("Input list file ",file," is not found - nothing to do")
                os._exit(-1)
            else :
                handle = open(file, "r", encoding="latin-1")
                list = handle.read().splitlines()
                handle.close()
        elif "-c" in line :
            cfgfile = sys.argv[iline]
            if not path.exists(cfgfile) :
                print("Config file ",cfgfile," is not found; using the default config")
                cfgfile = 'DOE.cfg'
        elif "-b" in line :
            if "Safari" in sys.argv[iline] :
                Safari = True
            else :
                Safari = False
else :
    print("Usage: python3 ",sys.argv[0]," -d DOI [--help]")
#-------------- reading config file ------------------------------
if path.exists(cfgfile) :
    cfg = open(cfgfile, "r", encoding="latin-1")
    configs = cfg.read().splitlines()
    cfg.close()
for term in configs :
    term = term.replace('"',"'")  # convert all double-quotes into single ones for easier parsing
    if '#' in term : # strip any comments
        term = term[0:term.find('#')-1]
    payload = term[term.find("'")+1:term.rfind("'")]
    identifier = term[0:term.find('=')].strip(' ');
    if 'institution' in identifier :
        institution = payload
    elif 'url' in identifier :
        url = payload
    elif 'grantID' in identifier :
        grantID = payload
    elif 'name' in identifier :
        name = payload
    elif 'email' in identifier :
        email = payload
    elif 'phone' in identifier :
        phone = payload
    elif 'office' in identifier :
        office = payload
    elif 'category' in identifier :
        category = payload
#--------- Printing configs
print('Running the script with the following parameters:')
print('Institution:',institution)
print('Grant number:',grantID)
print('Contact info: {}\n{}\n{}'.format(name,email,phone))

# Using Safari of Firefox to access web
if Safari :
  driver = webdriver.Safari();
else :
  driver = webdriver.Firefox();
if list == "" :
    list = doi.splitlines()
for doi in list :    # looping over the doi entries
    nTotal += 1
    inCDS = False
    info = parseDOI(doi)
    arXiv = info[0]
    journal = info[1]
    volume = info[2]
    year = info[3]
    page = info[4]
    doi = info[5]
    abstract = info[6]
    if arXiv == "" :
        if 'CERN' in abstract : # found CERN preprint
            arXiv = abstract
            CDS = getAbstractCDS(abstract)
            print('The arXiv entry is not found for doi:{}, but found a CDS preprnt {}'.format(doi,abstract))
            inCDS = True
    if arXiv == "" :
        if doi != '' :
            print('arXiv entry not found for doi:',doi,' - skipping this entry')
            failarXiv.append(doi)
        else :
            nTotal -= 1
    else :
        if inCDS :
            abstract = CDS[0]
            arXivURL = CDS[1]
        else :
            arXivURL = "http://arxiv.org/pdf/"+arXiv[arXiv.find(":")+1:len(arXiv)] + ".pdf"
            info = getInfoFromArXiv(info)
            if doi == "" and info[5] != "" :
                doi = info[5]
                print("Can't find the doi info in INSPIRE... Taking it from the arXiv:",doi,info[1])
            journal = info[1]
            volume = info[2]
            year = info[3]
            page = info[4]
            doi = info[5]
            abstract = info[6]
        if doi == "" or journal == "":
            print('doi entry not found for arXiv:',arXiv,' not a published manuscript - skipping this entry')
            failDOI.append(arXiv)
        else :
# Open the website
            print('DOI:{}; {}'.format(doi,arXiv),end = '...')
            driver.get(url)

            # Select the grant number box
            grant_box = driver.find_element_by_name('doe_contract_numbers')
            grant_box.send_keys(grantID)
            start_time = time.time()
            while grant_box.get_attribute('value') == '' :
                time.sleep(0.5)
                grant_box.send_keys(grantID)
                if time.time() - start_time > 10:
                    print("Grent ID field is not filled")
                    raise WebDriverException

            # Select the recipient box
            id_box = driver.find_element_by_name('researchorg')
            id_box.send_keys(institution)

            # Select the product type box
            id_product = Select(driver.find_element_by_name('prodtype'))
            id_product.select_by_visible_text('Accepted Manuscript of Journal Article')

            # Click the doi radio button
            #list = driver.find_element_by_id('isDoiAssoc1').click()

            element = driver.find_element_by_css_selector("input[type='radio'][value='Y']")
            driver.execute_script("arguments[0].click();", element)

            # Enter the doi number
            doi_box = driver.find_element_by_name('doi')
            doi_box.send_keys(doi)

            elem1= driver.find_element_by_xpath("//ul[@role='menu']")
            elem2= elem1.find_element_by_xpath(".//a[@href='#next']")
            driver.execute_script("arguments[0].click();", elem2)

            element = driver.find_element_by_id('journalname')
            journal = element.get_attribute('value')
            start_time = time.time()
            while journal == "" :
                time.sleep(0.5)
                journal = element.get_attribute('value')
                if time.time() - start_time > 10:
                    print("Journal field is not filled")
                    raise WebDriverException

            element = driver.find_element_by_id('pagerange')
            if element.get_attribute('value') == "":
                driver.execute_script("arguments[0].value = arguments[1]",element, page)

            elem1= driver.find_element_by_xpath("//ul[@role='menu']")
            elem2= elem1.find_element_by_xpath(".//a[@href='#next']")
            driver.execute_script("arguments[0].click();", elem2)

            start_time = time.time()    # Waiting for the authors to be filled by the DOE script
            element = driver.find_element_by_id('authorsTable_processing')
            if element != 0 :
                time.sleep(0.5)
                element = driver.find_element_by_id('authorsTable_processing')
                if time.time() - start_time > 30:
                    print("Author table is not filled")
                    raise WebDriverException

            elem1= driver.find_element_by_xpath("//ul[@role='menu']")
            elem2= elem1.find_element_by_xpath(".//a[@href='#next']")
            driver.execute_script("arguments[0].click();", elem2)

            # Fill the abstract
            element = driver.find_element_by_name('abstract')
            element = driver.find_element_by_xpath("//textarea[@class='form-control col-xs-12' and @id='abstract']")
            driver.execute_script("arguments[0].value = arguments[1]",element, abstract)

            # Select the sponsoring office
            if Safari : # work around the idiosyncrasy of the DOE script that doesn't comply with Safari
                element = driver.find_element_by_id('sponsor')
                driver.execute_script("arguments[0].click();", element)
                element.send_keys('')

            spon_product = Select(driver.find_element_by_xpath("//select[@class='form-control update_textarea col-xs-12' and @id='spon']"))
            spon_product.select_by_value(office)

            # Select the product type box
            id_product = Select(driver.find_element_by_id('cat'))
            id_product.select_by_value(category)

            elem1= driver.find_element_by_xpath("//ul[@role='menu']")
            elem2= elem1.find_element_by_xpath(".//a[@href='#next']")
            driver.execute_script("arguments[0].click();", elem2)

            elem1= driver.find_element_by_xpath("//ul[@role='menu']")
            elem2= elem1.find_element_by_xpath(".//a[@href='#next']")
            driver.execute_script("arguments[0].click();", elem2)

            # Select the Name and Position box

            name_box = driver.find_element_by_name('contact_name')
            driver.execute_script("arguments[0].value = arguments[1]",name_box, name)

            email_box = driver.find_element_by_name('contact_email')
            driver.execute_script("arguments[0].value = arguments[1]",email_box, email)

            phone_box = driver.find_element_by_name('contact_phone')
            driver.execute_script("arguments[0].value = arguments[1]",phone_box, phone)

            org_box = driver.find_element_by_name('contact_org')
            driver.execute_script("arguments[0].value = arguments[1]",org_box, institution)

            elem1= driver.find_element_by_xpath("//ul[@role='menu']")
            elem2= elem1.find_element_by_xpath(".//a[@href='#next']")
            driver.execute_script("arguments[0].click();", elem2)

            element = driver.find_element_by_css_selector("input[type='radio'][value='OFFSITE']")
            driver.execute_script("arguments[0].click();", element)

            element = driver.find_element_by_id('electronicavail')
            driver.execute_script("arguments[0].value = arguments[1]",element, arXivURL)

            element = driver.find_element_by_css_selector("input[type='radio'][value='PDFN']")
            driver.execute_script("arguments[0].click();", element)

            elem1= driver.find_element_by_xpath("//ul[@role='menu']")
            elem2= elem1.find_element_by_xpath(".//a[@href='#next']")
            driver.execute_script("arguments[0].click();", elem2)

            element = driver.find_element_by_id('ja_cert_1')
            driver.execute_script("arguments[0].click();", element)

            element = driver.find_element_by_id('ja_cert_2')
            driver.execute_script("arguments[0].click();", element)

            element = driver.find_element_by_id('ja_cert_3')
            driver.execute_script("arguments[0].click();", element)

            elem1= driver.find_element_by_xpath("//ul[@role='menu']")
            elem2= elem1.find_element_by_xpath(".//a[@href='#next']")
            driver.execute_script("arguments[0].click();", elem2)

            elem1= driver.find_element_by_xpath("//ul[@role='menu']")
            elem2= elem1.find_element_by_xpath(".//a[@href='#finish']")
            driver.execute_script("arguments[0].click();", elem2)

            success = False
            start_time = time.time()
            while time.time() - start_time < 20:
                elem1= driver.find_element_by_xpath("//div[@id='saveMsg']")
                if "Your submission was successful" in elem1.text :
                    success = True
                    break
                time.sleep(0.5)
            html_source = driver.page_source

            file_object = codecs.open(doi.replace('/','.')+'.html', 'w', 'utf-8')
            file_object.write(html_source)
            file_object.close()
            if success :
                nSuccess += 1
                print('Submision was sucessful')
            else :
                print('Problems with the submission; please check the {} file for more information'.format(doi.replace('/','.')+'.html'))
                failOther.append(doi)
driver.close()
print('Submission statistics:')
print('Attempted to submit {} paper(s): {} submitted successfully; {} submitted with errors'.format(nTotal,nSuccess,len(failOther)))
if len(failarXiv) > 0 :
    print('The following papers do not have arXiv entries and have not been sumbmitted:')
    for paper in failarXiv :
        print(paper)
if len(failDOI) > 0 :
    print('The following papers are not Accepted Publications and have not been sumbmitted:')
    for paper in failDOI :
      print(paper)
if len(failOther) > 0 :
    print('The following papers have failed submission:')
    for paper in failOther :
      print(paper)
