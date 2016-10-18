#! /usr/bin/env python
import sys
import os
import logging

def main():
    logFile = "E:/nimbietest/test.log"
    logging.basicConfig(filename=logFile, 
                            level=logging.DEBUG, 
                            format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Some info")
    logging.error("Something went wrong")
main()
