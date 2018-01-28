#!/usr/bin/env python3
#-*- coding: utf-8 -*-

# To use this script, make sure that geckodriver is in your path
# If you do not want to change the global path, you can just run
# PATH=$PATH:$(pwd)/geckodriver-v0.19.0-linux64 bash -c './scribd_downloader_3.py'

# Examples:
# 77 pages, different size:
# https://www.scribd.com/doc/236735923/3-Gelfand-Glagoleva-Kirilov-The-Method-of-coordinates-pdf
# 2 pages, music, one hidden
# https://www.scribd.com/doc/63942746/chopin-nocturne-n-20-partition
# others:
# https://www.scribd.com/document/359303091/A-Repository-of-Unix-History-and-Evolution
# https://www.scribd.com/document/31698781/Constitution-of-the-Mexican-Mafia-in-Texas

# TODO : auto download the geckodriver

import argparse
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import WebDriverException
from io import BytesIO
from PIL import Image
import time
from fpdf import FPDF
import os
import shutil

# Avoid useless warning about image size
try:
    Image.MAX_IMAGE_PIXELS = None
    warnings.simplefilter('ignore', Image.DecompressionBombWarning)
except: # Not sure if PIL (not Pillow) has these functions
    pass

def remove_class(driver, class_name):
    driver.execute_script("Array.from(document.getElementsByClassName('" + class_name + "')).forEach(function(x) {x.remove()});")

def add_css_property(driver, class_name, css_prop, css_value):
    command = "Array.from(document.getElementsByClassName('" + class_name + "')).forEach(function(x) {x.style." + css_prop + "=\"" + css_value + "\"});"
    driver.execute_script(command)

def clean_page(driver):
    # Remove the useless parts
    class_to_remove = ["sidebar_column",
                       "header_upper",
                       "toolbar_drop",
                       "between_page_ads",
                       "autogen_class_views_pdfs_upvote",
                       "page_blur_promo",
                       "autogen_class_views_pdfs_page_blur_promo",
                       "page_missing_explanation"]
    for class_name in class_to_remove:
        remove_class(driver, class_name)
    add_css_property(driver, "document_column", "position", "static")
    # add_css_property(driver, "document_scroller carousel_scroll_parent", "position", "static")
    add_css_property(driver, "no_scrolling", "overflowY", "visible")
    add_css_property(driver, "no_scrolling", "height", "auto")
    add_css_property(driver, "global_wrapper", "height", "auto")
    add_css_property(driver, "global_wrapper", "position", "static")
    add_css_property(driver, "global_wrapper", "overflow", "visible")
    add_css_property(driver, "document_scroller", "top", "0px")
    add_css_property(driver, "outer_page", "marginLeft", "0px")
    add_css_property(driver, "outer_page", "marginTop", "0px")
    add_css_property(driver, "outer_page", "marginBottom", "0px")
    add_css_property(driver, "document_container", "margin", "0px")
    # Allow blocked pages
    add_css_property(driver, "text_layer", "textShadow", "black 0 0 0px")
    add_css_property(driver, "absimg", "opacity", "1")

    
def take_one_big_screenshot(driver, filename_out, verbose=1, wait=1.0):
    ####### Download the pictures ######
    verbose = 1
    # Get total height of page
    js = 'var doc_scroller = $(".document_scroller")[0]; var scroll_height = Math.max(doc_scroller.scrollHeight, doc_scroller.clientHeight); return scroll_height;'
    scrollheight = driver.execute_script(js)
    size_scroll_window = driver.execute_script("""return $(".document_scroller")[0].clientHeight""")
    if verbose > 1:
        print("Scroll Height:")
        print(scrollheight)
        print("Size Scroll Window:")
        print(size_scroll_window)

    slices = []
    offset = 0
    last_img_size = size_scroll_window
    offset_arr=[]
    # Separate full screen in parts and make printscreens
    while offset < scrollheight:
        if verbose > 0:
            print("Taking screenshot : one more page...")
        if verbose > 1:
            print("Offset :" + str(offset))
            print("Last image size:" + str(last_img_size))

        # Scroll to size of page 
        if (scrollheight-offset)< last_img_size:
            # If part of screen is the last one, we need to
            # scroll just on rest of page
            command = "$(\".document_scroller\")[0].scrollTop = %s;" % (scrollheight - last_img_size)
            driver.execute_script(command)
            offset_arr.append(scrollheight - last_img_size)
        else:
            command = "$(\".document_scroller\")[0].scrollTop = %s;" % offset
            driver.execute_script(command)
            offset_arr.append(offset)

        clean_page(driver)
        # Better way?
        time.sleep(wait)
        
        # Creates image
        img = Image.open(BytesIO(driver.get_screenshot_as_png()))
        last_img_size = img.size[1]
        offset += last_img_size
        # Append new printscreen to array
        slices.append(img)
        if verbose > 1:
            driver.get_screenshot_as_file(temp_folder + '/screen_%s.jpg' % (offset))
    driver.execute_script("""alert("Please don't close this browser, it will be closed by itself at the end of the conversion. And don't close this box either or the brower may not close by itself.")""")

    # Create image with 
    screenshot = Image.new('RGB', (slices[0].size[0], scrollheight))
    offset = 0
    offset2= 0
    # Now glue all images together
    for img in slices:
        screenshot.paste(img, (0, offset_arr[offset2])) 
        offset += img.size[1]
        offset2+= 1      

    screenshot.save(filename_out)
    return screenshot
    
def main(scribd_url, final_pdf_output, verbose=1, wait=1.0):
    if verbose > 0:
        print("I will start the scraping...")
    # Create the temporary folder
    temp_folder = "scribd_downloader_tmp"
    shutil.rmtree(temp_folder, ignore_errors=True)
    os.mkdir(temp_folder)
    
    # Load selenium & firefox drivers
    if verbose > 0:
        print("Will load the webdriver for firefox...")
    try:
        driver = webdriver.Firefox()
    except WebDriverException as e:
        print("/!\\ ERROR /!\\")
        print(str(e))
        print("The script cannot find the executable 'geckodriver'.")
        print("Please, download it from the page:")
        print("  https://github.com/mozilla/geckodriver/releases")
        print("Extract it, and run again this script, by adding the")
        print("path of extraction via the tag '-p'.")
        print("""E.g: ./scribd_downloader_3.py -p geckodriver-v0.19.0-linux64 "https://www.scribd.com/document/31698781/Constitution-of-the-Mexican-Mafia-in-Texas" out.pdf""")
        exit(1)
    if verbose > 0:
        print("Webdriver loaded. Let us open the url.")

    # Loads the page
    driver.get(scribd_url)
    if verbose > 0:
        print("Page loaded. Will remove useless parts.")

    # Remove the useless parts
    clean_page(driver)
    if verbose > 0:
        print("Useless parts removed for the first time !")

    ####### Correct strange bug on zoom.... ######
    driver.set_window_size(800, 800)
    # driver.maximize_window() # Does not work with xvfb
    driver.set_window_size(1920, 1080)
    time.sleep(3)

    ####### Take a screenshot ######
    if verbose > 0:
        print("I will take the big screenshot...")
        big_out_picture_path = temp_folder + "/test_big_code.png"
    # TODO: would be nice to avoid the need of doing one big screenshot
    big_screenshot = take_one_big_screenshot(driver, big_out_picture_path, verbose=verbose, wait=wait)
    
    ####### Get the number of page ######
    nb_pages = driver.execute_script("""return Scribd.current_doc["page_count"]""")
    if verbose > 0:
        print("Number of pages: " + str(nb_pages))

    ####### Produce the output pdf ######
    pdf = FPDF()
    current_top=0
    for p in range(nb_pages):
        pdf.add_page()
        try:
            page_width = driver.execute_script("""return document.getElementById("outer_page_""" + str(p+1) + """").offsetWidth""")
            page_height = driver.execute_script("""return document.getElementById("outer_page_""" + str(p+1) + """").offsetHeight""")
        except:
            page_width = 1000
            page_height = 1294
        if verbose > 0:
            print("Page %d: %d x %d" % (p+1, page_width, page_height))
        crop_rectangle = (0, current_top, page_width, current_top + page_height)
        current_page_img = big_screenshot.crop(crop_rectangle)
        out_curr_filename = temp_folder + "/final_page_{0:04d}.png".format(p)
        current_page_img.save(out_curr_filename)
        if page_width/page_height < 210/297:
            pdf.image(out_curr_filename,
                      x = 0, y = 0, h = 297)
        else:
            pdf.image(out_curr_filename,
                      x = 0, y = 0, w = 210)
        current_top += page_height
    pdf.output(final_pdf_output, 'F')
        
    return(driver, big_screenshot)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Basic python script to download a PDF out of a scribd document')
    parser.add_argument("url",
                        metavar='URL',
                        help='The scribd url. E.g: "https://www.scribd.com/document/31698781/Constitution-of-the-Mexican-Mafia-in-Texas"')
    parser.add_argument("output_pdf",
                        metavar='OUT',
                        help='The output pdf file.')
    parser.add_argument("-v", "--verbose",
                        metavar='VERB',
                        type=int,
                        help='Verbosity, in 0-1',
                        default=1 )
    parser.add_argument("-p", "--path-geckodriver",
                        metavar='PATH',
                        help="The path of the folder containing the geckodriver folder if it's not already in the path",
                        default="."
                        )
    parser.add_argument("-w", "--wait-time",
                        metavar='WAIT',
                        type=float,
                        help='The time to wait between each screenshot in seconds (float accepted)',
                        default=1.0 )
    args = parser.parse_args()
    if args.path_geckodriver:
        os.environ["PATH"] += os.pathsep + os.path.abspath(args.path_geckodriver)
    print("Scraping url: " + args.url)
    print("Output: " + args.output_pdf)
    (driver,_) = main(args.url, args.output_pdf, verbose=args.verbose, wait=args.wait_time)
    print("The pdf has been succesfully created in " + args.output_pdf + " !")
    try:
        alert = driver.switch_to.alert
        alert.accept()
    except:
        pass
    driver.close()
