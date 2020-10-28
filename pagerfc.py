#!/usr/bin/env python3
#
# add page breaks to a v3 text rfc
# and splice page numbers into the table of contents

import re
from random import randint
import sys

class Pagerfc:

    def __init__(self, file, debug=False):
        if type(file) == str:
            with open(file, "r", encoding="utf-8") as f:
                self.lines = [ l.rstrip() for l in f ]
        else:
            self.lines = [ l.rstrip() for l in file ]
        self.debug = debug

    def findtitle(self):
        """
        find the title and RFC number and date
        first indented line
        could be continued but we don't care
        """
        for l in self.lines:
            r = re.match(r'Request for Comments: *(\d+)', l)
            if r:
                self.rfcno = r.group(1)
            r = re.match(r'.* 20\d\d$', l[-15:])
            if r:
                self.rfcdate = l[-15:].strip()

            if l and l[0] == ' ':
                self.title = l.strip()
                return
        self.title = None

    def findtoc(self):
        """
        find the TOC entries to add page numbers
        """
        toc = None 
        intoc = 0                       # 0 initially 1 after TOC header, 1 in TOC
        for l in self.lines:
            if intoc == 0:
                if l == 'Table of Contents':
                    intoc = 1
                    continue
            elif intoc == 1:
                if l > '':
                    toc = [ l ]
                    intoc = 2
            else:
                if l == '':
                    break
                toc.append(l)
        if toc:
            self.toc = { l.replace(' ',''): None for l in toc } # squeeze out spaces

    def makepages(self):
        """
        break into pages, add TOC page numbers along the way
        """
        pageno = 1
        thishdr = None
        thispage = []
        self.pages = [ thispage ]
        self.sechdrs = []              # section at the end of the page

        def dotoc(l):
            """
            put a page number into the TOC
            """
            ls = l.replace(' ','')
            if ls in self.toc:
                self.toc[ls] = pageno
            else:   # hack for very long TOC entries
                pref = l.split()[0]
                for k in self.toc:
                    if k.startswith(pref):
                        self.toc[k] = pageno

        for li in range(len(self.lines)):
            l = self.lines[li]

            # kill BOM
            if '\ufeff' in l:
                l = ''
            # start a new page ?
            if len(thispage) > randint(56,58):
                # would there be a widow?
                if l > '' and self.lines[li+1] == '' and self.lines[li-1] > '':
                    if self.debug:
                        #print(self.lines[li-1: li+2])
                        print("avoided widow", pageno)
                else:
                    self.sechdrs.append(thishdr)
                    lastpage = thispage
                    thispage = []
                    # was there an orphan
                    if l > '' and self.lines[li-1] > '' and self.lines[li-2] == '':
                        if self.debug:
                            #print(self.lines[li-2: li+1])
                            print("moved orphan", pageno)
                        # move it onto the new page
                        lx = lastpage.pop()
                        # adjust page ref if needed
                        if not lx.startswith(' '):
                            dotoc(lx)
                        thispage.append(lx)
                    self.pages.append(thispage)
                    pageno += 1
            
            thispage.append(l)

            # section header? line starts with a non-space
            if l and not l.startswith(' '):
                dotoc(l)
                thishdr = l

        self.sechdrs.append(thishdr)
                
    def printpages(self, file=sys.stdout):
        """
        format and print each page
        """
        seentoc = 0                     # 0 not yet, 1 in TOC hdr, 2 in toc, 3 past toc
        for pageno, hdr, page in zip(range(1, 1+len(self.pages)), self.sechdrs, self.pages):
            if pageno > 1:
                print(f"RFC {self.rfcno} {self.title}\n", file=file)
            else:
                print("\ufeff", file=file) # start with a BOM

            for l in page:
                if seentoc == 0 and l == 'Table of Contents':
                    seentoc = 1
                elif seentoc == 1:
                    if l:
                        seentoc = 2
                if seentoc == 2:
                    if not l:
                        seentoc = 3
                    elif l.replace(' ','') in self.toc:
                        tpn = self.toc[l.replace(' ','')]
                        padlen = 70 - len(l) - len(str(tpn))
                        if tpn:
                            l =  f"{l} {padlen * '.'} {tpn}"
                    else:
                        print("??? mystery toc",l)
                print(l, file=file)
            # even up pages
            if len(page) < 58:
                print((57 - len(page)) * '\n', file=file)
            pagestr = f"[Page {pageno}]"
            padlen = 72-len(pagestr)-len(hdr)
            print(f"\n{hdr}{padlen * ' '}{pagestr}\n\f", file=file)


if __name__=="__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Paginate text RFCs')
    parser.add_argument("-d", action='store_true', help='debug stuff')
    parser.add_argument("-o", type=str, help='output file')
    parser.add_argument("file", type=str, help='file to paginate')
    args = parser.parse_args()

    pp = Pagerfc(args.file, debug=args.d)
    pp.findtitle()
    pp.findtoc()
    pp.makepages()
    if args.o:
        with open(args.o, "w") as fo:
            pp.printpages(file=fo)
    else:
        pp.printpages()



            
