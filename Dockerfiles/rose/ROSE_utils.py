#!/usr/bin/python
import os
import re

from string import *
import sys
import subprocess
import datetime

from collections import defaultdict

#SET OF UTILITY FUNCTIONS FOR mapEnhancerFromFactor.py

#==================================================================
#==========================I/O FUNCTIONS===========================
#==================================================================

#unParseTable 4/14/08
#takes in a table generated by parseTable and writes it to an output file
#takes as parameters (table, output, sep), where sep is how the file is delimited
#example call unParseTable(table, 'table.txt', '\t') for a tab del file

def unParseTable(table, output, sep):
    fh_out = open(output,'w')
    if len(sep) == 0:
        for i in table:
            fh_out.write(str(i))
            fh_out.write('\n')
    else:
        for line in table:
            line = [str(x) for x in line]
            line = join(line,sep)

            fh_out.write(line)
            fh_out.write('\n')

    fh_out.close()

#parseTable 4/14/08
#takes in a table where columns are separated by a given symbol and outputs
#a nested list such that list[row][col]
#example call:
#table = parseTable('file.txt','\t')
def parseTable(fn, sep, header = False,excel = False):
    fh = open(fn)
    if header == True:
        header = fh.readline() #disposes of the header

    table = []
    for line in fh:
        line = line.rstrip().split(sep)
        table.append(line)

    fh.close()

    return table


def formatBed(bed,output=''):

    '''
    formats a bed file from UCSC or MACS into a WUSTL gateway compatible bed
    '''


    newBed = []

    if type(bed) == str:
        bed = parseTable(bed,'\t')

    indexTicker = 1
    for line in bed:

        newLine = line[0:4]
        try:
            strand = line[5]
        except IndexError:
            strand = '.'
        newLine+= [indexTicker,strand]
        indexTicker +=1
        newBed.append(newLine)

    if len(output) > 0:
        unParseTable(newBed,output,'\t')
    else:
        return newBed



def bedToGFF(bed,output=''):

    '''
    turns a bed into a gff file
    '''
    if type(bed) == str:
        bed = parseTable(bed,'\t')

    bed = formatBed(bed)

    gff = []
    for line in bed:
        gffLine = [line[0],line[3],'',line[1],line[2],line[4],line[5],'',line[3]]
        gff.append(gffLine)

    if len(output) > 0:
        unParseTable(gff,output,'\t')
    else:
        return gff


#100912
#gffToBed

def gffToBed(gff,output= ''):
    '''
    turns a gff to a bed file
    '''
    bed = []
    indexTicker = 1
    for line in gff:
        newLine = [line[0],line[3],line[4],line[1],indexTicker,line[6]]
        indexTicker+=1
        bed.append(newLine)
    if len(output) == 0:
        return bed
    else:
        unParseTable(bed,output,'\t')

def formatFolder(folderName,create=False):

    '''
    makes sure a folder exists and if not makes it
    returns a bool for folder
    '''

    if folderName[-1] != '/':
        folderName +='/'

    try:
        foo = os.listdir(folderName)
        return folderName
    except OSError:
        print('folder %s does not exist' % (folderName))
        if create:
            os.system('mkdir %s' % (folderName))
            return folderName
        else:

            return False



#==================================================================
#===================ANNOTATION FUNCTIONS===========================
#==================================================================


def makeStartDict(annotFile,geneList = []):
    '''
    makes a dictionary keyed by refseq ID that contains information about
    chrom/start/stop/strand/common name
    '''

    if type(geneList) == str:
        geneList = parseTable(geneList,'\t')
        geneList = [line[0] for line in geneList]

    if upper(annotFile).count('REFSEQ') == 1:
        refseqTable,refseqDict = importRefseq(annotFile)
        if len(geneList) == 0:
            geneList = refseqDict.keys()
        startDict = {}
        for gene in geneList:
            if refseqDict.has_key(gene) == False:
                continue
            startDict[gene]={}
            startDict[gene]['sense'] = refseqTable[refseqDict[gene][0]][3]
            startDict[gene]['chr'] = refseqTable[refseqDict[gene][0]][2]
            startDict[gene]['start'] = getTSSs([gene],refseqTable,refseqDict)
            if startDict[gene]['sense'] == '+':
                startDict[gene]['end'] =[int(refseqTable[refseqDict[gene][0]][5])]
            else:
                startDict[gene]['end'] = [int(refseqTable[refseqDict[gene][0]][4])]
            startDict[gene]['name'] = refseqTable[refseqDict[gene][0]][12]
    return startDict


#generic function to get the TSS of any gene
def getTSSs(geneList,refseqTable,refseqDict):
    #refseqTable,refseqDict = importRefseq(refseqFile)
    if len(geneList) == 0:
        refseq = refseqTable
    else:
        refseq = refseqFromKey(geneList,refseqDict,refseqTable)
    TSS = []
    for line in refseq:
        if line[3] == '+':
            TSS.append(line[4])
        if line[3] == '-':
            TSS.append(line[5])
    TSS = map(int,TSS)

    return TSS


#12/29/08
#refseqFromKey(refseqKeyList,refseqDict,refseqTable)
#function that grabs refseq lines from refseq IDs
def refseqFromKey(refseqKeyList,refseqDict,refseqTable):
    typeRefseq = []
    for name in refseqKeyList:
        if refseqDict.has_key(name):
            typeRefseq.append(refseqTable[refseqDict[name][0]])
    return typeRefseq



#10/13/08
#importRefseq
#takes in a refseq table and makes a refseq table and a refseq dictionary for keying the table

def importRefseq(refseqFile, returnMultiples = False):

    '''
    opens up a refseq file downloaded by UCSC
    '''
    refseqTable = parseTable(refseqFile,'\t')
    refseqDict = {}
    ticker = 1
    for line in refseqTable[1:]:
        if refseqDict.has_key(line[1]):
            refseqDict[line[1]].append(ticker)
        else:
            refseqDict[line[1]] = [ticker]
        ticker = ticker + 1

    multiples = []
    for i in refseqDict:
        if len(refseqDict[i]) > 1:
            multiples.append(i)

    if returnMultiples == True:
        return refseqTable,refseqDict,multiples
    else:
        return refseqTable,refseqDict


#==================================================================
#========================LOCUS INSTANCE============================
#==================================================================

#Locus and LocusCollection instances courtesy of Graham Ruby


class Locus:
    # this may save some space by reducing the number of chromosome strings
    # that are associated with Locus instances (see __init__).
    __chrDict = dict()
    __senseDict = {'+':'+', '-':'-', '.':'.'}
    # chr = chromosome name (string)
    # sense = '+' or '-' (or '.' for an ambidexterous locus)
    # start,end = ints of the start and end coords of the locus;
    #      end coord is the coord of the last nucleotide.
    def __init__(self,chr,start,end,sense,ID=''):
        coords = [int(start),int(end)]
        coords.sort()
        # this method for assigning chromosome should help avoid storage of
        # redundant strings.
        if not(self.__chrDict.has_key(chr)): self.__chrDict[chr] = chr
        self._chr = self.__chrDict[chr]
        self._sense = self.__senseDict[sense]
        self._start = int(coords[0])
        self._end = int(coords[1])
        self._ID = ID
    def ID(self): return self._ID
    def chr(self): return self._chr
    def start(self): return self._start  ## returns the smallest coordinate
    def end(self): return self._end   ## returns the biggest coordinate
    def len(self): return self._end - self._start + 1
    def getAntisenseLocus(self):
        if self._sense=='.': return self
        else:
            switch = {'+':'-', '-':'+'}
            return Locus(self._chr,self._start,self._end,switch[self._sense])
    def coords(self): return [self._start,self._end]  ## returns a sorted list of the coordinates
    def sense(self): return self._sense
    # returns boolean; True if two loci share any coordinates in common
    def overlaps(self,otherLocus):
        if self.chr()!=otherLocus.chr(): return False
        elif not(self._sense=='.' or \
                 otherLocus.sense()=='.' or \
                 self.sense()==otherLocus.sense()): return False
        elif self.start() > otherLocus.end() or otherLocus.start() > self.end(): return False
        else: return True

    # returns boolean; True if all the nucleotides of the given locus overlap
    #      with the self locus
    def contains(self,otherLocus):
        if self.chr()!=otherLocus.chr(): return False
        elif not(self._sense=='.' or \
                 otherLocus.sense()=='.' or \
                 self.sense()==otherLocus.sense()): return False
        elif self.start() > otherLocus.start() or otherLocus.end() > self.end(): return False
        else: return True

    # same as overlaps, but considers the opposite strand
    def overlapsAntisense(self,otherLocus):
        return self.getAntisenseLocus().overlaps(otherLocus)
    # same as contains, but considers the opposite strand
    def containsAntisense(self,otherLocus):
        return self.getAntisenseLocus().contains(otherLocus)
    def __hash__(self): return self._start + self._end
    def __eq__(self,other):
        if self.__class__ != other.__class__: return False
        if self.chr()!=other.chr(): return False
        if self.start()!=other.start(): return False
        if self.end()!=other.end(): return False
        if self.sense()!=other.sense(): return False
        return True
    def __ne__(self,other): return not(self.__eq__(other))
    def __str__(self): return self.chr()+'('+self.sense()+'):'+'-'.join(map(str,self.coords()))
    def checkRep(self):
        pass


class LocusCollection:
    def __init__(self,loci,windowSize):
        ### top-level keys are chr, then strand, no space
        self.__chrToCoordToLoci = dict()
        self.__loci = dict()
        self.__winSize = windowSize
        for lcs in loci: self.__addLocus(lcs)

    def __addLocus(self,lcs):
        if not(self.__loci.has_key(lcs)):
            self.__loci[lcs] = None
            if lcs.sense()=='.': chrKeyList = [lcs.chr()+'+', lcs.chr()+'-']
            else: chrKeyList = [lcs.chr()+lcs.sense()]
            for chrKey in chrKeyList:
                if not(self.__chrToCoordToLoci.has_key(chrKey)): self.__chrToCoordToLoci[chrKey] = dict()
                for n in self.__getKeyRange(lcs):
                    if not(self.__chrToCoordToLoci[chrKey].has_key(n)): self.__chrToCoordToLoci[chrKey][n] = []
                    self.__chrToCoordToLoci[chrKey][n].append(lcs)

    def __getKeyRange(self,locus):
        start = locus.start() / self.__winSize
        end = locus.end() / self.__winSize + 1 ## add 1 because of the range
        return range(start,end)

    def __len__(self): return len(self.__loci)

    def append(self,new): self.__addLocus(new)
    def extend(self,newList):
        for lcs in newList: self.__addLocus(lcs)
    def hasLocus(self,locus):
        return self.__loci.has_key(locus)
    def remove(self,old):
        if not(self.__loci.has_key(old)): raise ValueError("requested locus isn't in collection")
        del self.__loci[old]
        if old.sense()=='.': senseList = ['+','-']
        else: senseList = [old.sense()]
        for k in self.__getKeyRange(old):
            for sense in senseList:
                self.__chrToCoordToLoci[old.chr()+sense][k].remove(old)

    def getWindowSize(self): return self.__winSize
    def getLoci(self): return self.__loci.keys()
    def getChrList(self):
        # i need to remove the strand info from the chromosome keys and make
        # them non-redundant.
        tempKeys = dict()
        for k in self.__chrToCoordToLoci.keys(): tempKeys[k[:-1]] = None
        return tempKeys.keys()

    def __subsetHelper(self,locus,sense):
        sense = sense.lower()
        if ['sense','antisense','both'].count(sense)!=1:
            raise ValueError("sense command invalid: '"+sense+"'.")
        matches = dict()
        senses = ['+','-']
        if locus.sense()=='.' or sense=='both': lamb = lambda s: True
        elif sense=='sense': lamb = lambda s: s==locus.sense()
        elif sense=='antisense': lamb = lambda s: s!=locus.sense()
        else: raise ValueError("sense value was inappropriate: '"+sense+"'.")
        for s in filter(lamb, senses):
            chrKey = locus.chr()+s
            if self.__chrToCoordToLoci.has_key(chrKey):
                for n in self.__getKeyRange(locus):
                    if self.__chrToCoordToLoci[chrKey].has_key(n):
                        for lcs in self.__chrToCoordToLoci[chrKey][n]:
                            matches[lcs] = None
        return matches.keys()

    # sense can be 'sense' (default), 'antisense', or 'both'
    # returns all members of the collection that overlap the locus
    def getOverlap(self,locus,sense='sense'):
        matches = self.__subsetHelper(locus,sense)
        ### now, get rid of the ones that don't really overlap
        realMatches = dict()
        if sense=='sense' or sense=='both':
            for i in filter(lambda lcs: lcs.overlaps(locus), matches):
                realMatches[i] = None
        if sense=='antisense' or sense=='both':
            for i in filter(lambda lcs: lcs.overlapsAntisense(locus), matches):
                realMatches[i] = None
        return realMatches.keys()

    # sense can be 'sense' (default), 'antisense', or 'both'
    # returns all members of the collection that are contained by the locus
    def getContained(self,locus,sense='sense'):
        matches = self.__subsetHelper(locus,sense)
        ### now, get rid of the ones that don't really overlap
        realMatches = dict()
        if sense=='sense' or sense=='both':
            for i in filter(lambda lcs: locus.contains(lcs), matches):
                realMatches[i] = None
        if sense=='antisense' or sense=='both':
            for i in filter(lambda lcs: locus.containsAntisense(lcs), matches):
                realMatches[i] = None
        return realMatches.keys()

    # sense can be 'sense' (default), 'antisense', or 'both'
    # returns all members of the collection that contain the locus
    def getContainers(self,locus,sense='sense'):
        matches = self.__subsetHelper(locus,sense)
        ### now, get rid of the ones that don't really overlap
        realMatches = dict()
        if sense=='sense' or sense=='both':
            for i in filter(lambda lcs: lcs.contains(locus), matches):
                realMatches[i] = None
        if sense=='antisense' or sense=='both':
            for i in filter(lambda lcs: lcs.containsAntisense(locus), matches):
                realMatches[i] = None
        return realMatches.keys()

    def stitchCollection(self,stitchWindow=1,sense='both'):

        '''
        reduces the collection by stitching together overlapping loci
        returns a new collection
        '''

        #initializing stitchWindow to 1
        #this helps collect directly adjacent loci



        locusList = self.getLoci()
        oldCollection = LocusCollection(locusList,500)

        stitchedCollection = LocusCollection([],500)

        for locus in locusList:
            #print(locus.coords())
            if oldCollection.hasLocus(locus):
                oldCollection.remove(locus)
                overlappingLoci = oldCollection.getOverlap(Locus(locus.chr(),locus.start()-stitchWindow,locus.end()+stitchWindow,locus.sense(),locus.ID()),sense)

                stitchTicker = 1
                while len(overlappingLoci) > 0:
                    stitchTicker+=len(overlappingLoci)
                    overlapCoords = locus.coords()


                    for overlappingLocus in overlappingLoci:
                        overlapCoords+=overlappingLocus.coords()
                        oldCollection.remove(overlappingLocus)
                    if sense == 'both':
                        locus = Locus(locus.chr(),min(overlapCoords),max(overlapCoords),'.',locus.ID())
                    else:
                        locus = Locus(locus.chr(),min(overlapCoords),max(overlapCoords),locus.sense(),locus.ID())
                    overlappingLoci = oldCollection.getOverlap(Locus(locus.chr(),locus.start()-stitchWindow,locus.end()+stitchWindow,locus.sense()),sense)
                locus._ID = '%s_%s_lociStitched' % (stitchTicker,locus.ID())

                stitchedCollection.append(locus)

            else:
                continue
        return stitchedCollection



#==================================================================
#========================LOCUS FUNCTIONS===========================
#==================================================================
#06/11/09
#turns a locusCollection into a gff
#does not write to disk though
def locusCollectionToGFF(locusCollection):
    lociList = locusCollection.getLoci()
    gff = []
    for locus in lociList:
        newLine = [locus.chr(),locus.ID(),'',locus.coords()[0],locus.coords()[1],'',locus.sense(),'',locus.ID()]
        gff.append(newLine)
    return gff


def gffToLocusCollection(gff,window =500):

    '''
    opens up a gff file and turns it into a LocusCollection instance
    '''

    lociList = []
    if type(gff) == str:
        gff = parseTable(gff,'\t')


    nameList = []
    for line in gff:
        #USE line[2] as the locus ID.  If that is empty use line[8]
        if len(line) < 7:
            print('SKIPPING THIS LINE')
            print(line)
            continue


        if line[0][0] == '#':
            continue

        if len(line[1]) > 0:
            name = line[1]
        elif len(line[8]) >0:
            name = line[8]
        else:
            name = '%s:%s:%s-%s' % (line[0],line[6],line[3],line[4])
        nameList.append(name)
        lociList.append(Locus(line[0],line[3],line[4],line[6],name))

    #check that all the names are unique
    if len(nameList) != len(uniquify(nameList)):
        print('ERROR: FOR GFFS, ALL REGIONS MUST HAVE A UNIQUE IDENTIFIER IN COLUMN 2')
        sys.exit()
    return LocusCollection(lociList,window)


#maketranscriptCollection
#04/07/09
#makes a LocusCollection w/ each transcript as a locus
#bob = makeTranscriptCollection('/Users/chazlin/genomes/mm8/mm8refseq.txt')
def makeTranscriptCollection(annotFile,upSearch,downSearch,window = 500,geneList = []):
    '''
    makes a LocusCollection w/ each transcript as a locus
    takes in a refseqfile
    '''

    if upper(annotFile).count('REFSEQ') == 1:
        refseqTable,refseqDict = importRefseq(annotFile)
        locusList = []
        ticker = 0
        if len(geneList) == 0:
            geneList =refseqDict.keys()
        for line in refseqTable[1:]:
            if geneList.count(line[1]) > 0:
                if line[3] == '-':
                    locus = Locus(line[2],int(line[4])-downSearch,int(line[5])+upSearch,line[3],line[1])
                else:
                    locus = Locus(line[2],int(line[4])-upSearch,int(line[5])+downSearch,line[3],line[1])
                locusList.append(locus)
                ticker = ticker + 1
                if ticker%1000 == 0:
                    print(ticker)


    transCollection = LocusCollection(locusList,window)

    return transCollection



def makeTSSLocus(gene,startDict,upstream,downstream):
    '''
    given a startDict, make a locus for any gene's TSS w/ upstream and downstream windows
    '''

    start = startDict[gene]['start'][0]
    if startDict[gene]['sense'] =='-':
        return Locus(startDict[gene]['chr'],start-downstream,start+upstream,'-',gene)
    else:
        return Locus(startDict[gene]['chr'],start-upstream,start+downstream,'+',gene)


#06/11/09
#takes a locus and expands it by a fixed upstream/downstream amount. spits out the new larger locus
def makeSearchLocus(locus,upSearch,downSearch):
    if locus.sense() == '-':
        searchLocus = Locus(locus.chr(),locus.start()-downSearch,locus.end()+upSearch,locus.sense(),locus.ID())
    else:
        searchLocus = Locus(locus.chr(),locus.start()-upSearch,locus.end()+downSearch,locus.sense(),locus.ID())
    return searchLocus


#==================================================================
#==========================BAM CLASS===============================
#==================================================================

#11/11/10
#makes a new class Bam for dealing with bam files and integrating them into the SolexaRun class


def checkChrStatus(bamFile):
    command = 'samtools view %s | head -n 1' % (bamFile)
    #print "TESTING"
    #print command
    stats = subprocess.Popen(command,stdin = subprocess.PIPE,stderr = subprocess.PIPE,stdout = subprocess.PIPE,shell = True)
    statLines = stats.stdout.readlines()
    stats.stdout.close()
    chrPattern = re.compile('chr')
    for line in statLines:
      #print line
      sline = line.split("\t")
      #print sline[2]
      if re.search(chrPattern, sline[2]):
	return 1
      else:
	return 0

def convertBitwiseFlag(flag):
   if int(flag) & 16:
	return "-";
   else:
	return "+";

class Bam:
    '''A class for a sorted and indexed bam file that allows easy analysis of reads'''
    def __init__(self,bamFile):
        self._bam = bamFile



    def getTotalReads(self,readType = 'mapped'):
        command = 'samtools flagstat %s' % (self._bam)
        stats = subprocess.Popen(command,stdin = subprocess.PIPE,stderr = subprocess.PIPE,stdout = subprocess.PIPE,shell = True)
        statLines = stats.stdout.readlines()
        stats.stdout.close()
        if readType == 'mapped':
            for line in statLines:
                if line.count('mapped (') == 1:

                    return int(line.split(' ')[0])
        if readType == 'total':
            return int(statLines[0].split(' ')[0])

    def convertBitwiseFlag(self,flag):
      if flag & 16:
	return "-";
      else:
	return "+";

    def getRawReads(self,locus,sense,unique = False,includeJxnReads = False,printCommand = False):
        '''
        gets raw reads from the bam using samtools view.
        can enforce uniqueness and strandedness
        '''
        locusLine = locus.chr()+':'+str(locus.start())+'-'+str(locus.end())

        command = 'samtools view %s %s' % (self._bam,locusLine)
        if printCommand:
            print(command)
        getReads = subprocess.Popen(command,stdin = subprocess.PIPE,stderr = subprocess.PIPE,stdout = subprocess.PIPE,shell = True)
        reads = getReads.communicate()
        reads = reads[0].split('\n')[:-1]
        reads = [read.split('\t') for read in reads]
        if includeJxnReads == False:
            reads = filter(lambda x: x[5].count('N') < 1,reads)

        #convertDict = {'16':'-','0':'+','64':'+','65':'+','80':'-','81':'-','129':'+','145':'-'}
        convertDict = {'16':'-','0':'+','64':'+','65':'+','80':'-','81':'-','129':'+','145':'-','256':'+','272':'-','99':'+','147':'-'}


        #BJA added 256 and 272, which correspond to 0 and 16 for multi-mapped reads respectively:
        #http://onetipperday.blogspot.com/2012/04/understand-flag-code-of-sam-format.html
        #convert = string.maketrans('160','--+')
        keptReads = []
        seqDict = defaultdict(int)
        if sense == '-':
          strand = ['+','-']
          strand.remove(locus.sense())
          strand = strand[0]
        else:
            strand = locus.sense()
        for read in reads:
            #readStrand = read[1].translate(convert)[0]
	    #print read[1], read[0]
            #readStrand = convertDict[read[1]]
            readStrand = convertBitwiseFlag(read[1])

            if sense == 'both' or sense == '.' or readStrand == strand:

                if unique and seqDict[read[9]] == 0:
                    keptReads.append(read)
                elif not unique:
                    keptReads.append(read)
            seqDict[read[9]]+=1

        return keptReads

    def readsToLoci(self,reads,IDtag = 'sequence,seqID,none'):
        '''
        takes raw read lines from the bam and converts them into loci
        '''
        loci = []
        ID = ''
        if IDtag == 'sequence,seqID,none':
            print('please specify one of the three options: sequence, seqID, none')
            return
        #convert = string.maketrans('160','--+')
        #convertDict = {'16':'-','0':'+','64':'+','65':'+','80':'-','81':'-','129':'+','145':'-'}
	#convertDict = {'16':'-','0':'+','64':'+','65':'+','80':'-','81':'-','129':'+','145':'-','256':'+','272':'-'}

        #BJA added 256 and 272, which correspond to 0 and 16 for multi-mapped reads respectively:
        #http://onetipperday.blogspot.com/2012/04/understand-flag-code-of-sam-format.html
        #convert = string.maketrans('160','--+')
        numPattern = re.compile('\d*')
        for read in reads:
            chrom = read[2]
            #strand = read[1].translate(convert)[0]
            #strand = convertDict[read[1]]
            strand = convertBitwiseFlag(read[1])
            if IDtag == 'sequence':
                ID = read[9]
            elif IDtag == 'seqID':
                ID = read[0]
            else:
                ID = ''

            length = len(read[9])
            start = int(read[3])
            if read[5].count('N') == 1:
                #this awful oneliner first finds all of the numbers in the read string
                #then it filters out the '' and converts them to integers
                #only works for reads that span one junction

                [first,gap,second] = [int(x) for x in filter(lambda x: len(x) > 0, re.findall(numPattern,read[5]))][0:3]
                if IDtag == 'sequence':
                    loci.append(Locus(chrom,start,start+first,strand,ID[0:first]))
                    loci.append(Locus(chrom,start+first+gap,start+first+gap+second,strand,ID[first:]))
                else:
                    loci.append(Locus(chrom,start,start+first,strand,ID))
                    loci.append(Locus(chrom,start+first+gap,start+first+gap+second,strand,ID))
            elif read[5].count('N') > 1:
                continue
            else:
                loci.append(Locus(chrom,start,start+length,strand,ID))
        return loci

    def getReadsLocus(self,locus,sense = 'both',unique = True,IDtag = 'sequence,seqID,none',includeJxnReads = False):
        '''
        gets all of the reads for a given locus
        '''
        reads = self.getRawReads(locus,sense,unique,includeJxnReads)

        loci = self.readsToLoci(reads,IDtag)

        return loci

    def getReadSequences(self,locus,sense = 'both',unique = True,includeJxnReads = False):

        reads = self.getRawReads(locus,sense,unique,includeJxnReads)

        return [read[9] for read in reads]

    def getReadStarts(self,locus,sense = 'both',unique = False,includeJxnReads = False):
        reads = self.getRawReads(locus,sense,unique,includeJxnReads)

        return [int(read[3]) for read in reads]


    def getReadCount(self,locus,sense = 'both',unique = True,includeJxnReads = False):
        reads = self.getRawReads(locus,sense,unique,includeJxnReads)

        return len(reads)



#==================================================================
#========================MISC FUNCTIONS============================
#==================================================================




#uniquify function
#by Peter Bengtsson
#Used under a creative commons license
#sourced from  here: http://www.peterbe.com/plog/uniqifiers-benchmark

def uniquify(seq, idfun=None):
    # order preserving
    if idfun is None:
        def idfun(x): return x
    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        # in old Python versions:
        # if seen.has_key(marker)
        # but in new ones:
        if marker in seen: continue
        seen[marker] = 1
        result.append(item)
    return result


#082009
#taken from http://code.activestate.com/recipes/491268/

def order(x, NoneIsLast = True, decreasing = False):
    """
    Returns the ordering of the elements of x. The list
    [ x[j] for j in order(x) ] is a sorted version of x.

    Missing values in x are indicated by None. If NoneIsLast is true,
    then missing values are ordered to be at the end.
    Otherwise, they are ordered at the beginning.
    """
    omitNone = False
    if NoneIsLast == None:
        NoneIsLast = True
        omitNone = True

    n  = len(x)
    ix = range(n)
    if None not in x:
        ix.sort(reverse = decreasing, key = lambda j : x[j])
    else:
        # Handle None values properly.
        def key(i, x = x):
            elem = x[i]
            # Valid values are True or False only.
            if decreasing == NoneIsLast:
                return not(elem is None), elem
            else:
                return elem is None, elem
        ix = range(n)
        ix.sort(key=key, reverse=decreasing)

    if omitNone:
        n = len(x)
        for i in range(n-1, -1, -1):
            if x[ix[i]] == None:
                n -= 1
        return ix[:n]
    return ix
