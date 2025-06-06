#! /usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import pathlib
import pandas as pd

__version__ = '0.10.0'

def print_and_exec_shell(command):
    print (command)
    os.system(command)

def check_file(file):
    if os.path.isfile(file):
        pass
    else:
        print ("Error: " + file + " does not exist.")
        exit()

def check_dir(dir):
    if os.path.isdir(dir):
        pass
    else:
        print ("Error: " + dir + " does not exist.")
        exit()

def get_mapfile_postfix(mapparam):
    post = mapparam.replace(' ', '')
    return post

def do_qualitycheck_fastq(fastq, fastqcdir, fastpdir):
    prefix = os.path.basename(fastq).replace('.fastq', '').replace('.gz', '').replace('.fq', '')
    fastqc_output = fastqcdir + prefix + "_fastqc.zip"
    fastp_output = fastpdir + prefix + ".fastp.json"

    if os.path.isfile(fastqc_output):
        print (fastqc_output + " already created. skipping.")
    else:
        print_and_exec_shell('fastqc -t 4 -o ' + fastqcdir + ' ' + fastq)

    if os.path.isfile(fastp_output):
        print (fastp_output + " already created. skipping.")
    else:
        print_and_exec_shell('fastp -w 4 -q 15 -n 5 -i ' + fastq
                             + ' -h ' + fastpdir + prefix + '.fastp.html'
                             + ' -j ' + fastpdir + prefix + '.fastp.json')

def do_fastqc(chdir, build, samplelist):
    fastqcdir = chdir + "/fastqc/"
    fastpdir =  chdir + "/fastp/"
    os.makedirs(fastqcdir, exist_ok=True)
    os.makedirs(fastpdir, exist_ok=True)

    df = pd.read_csv(samplelist, sep="\t", header=None)
    df.fillna("", inplace=True)
    for index, row in df.iterrows():
        if (len(row)<2 or row[1] == ""):
            print ("Error: specify fastq file in " + samplelist + ".")
            exit()

        prefix = row[0]
        fq1 = row[1]
        for fastq in fq1.split(","):
            do_qualitycheck_fastq(fastq, fastqcdir, fastpdir)

        if (len(row)>2): # for paired-end
            fq2 = row[2]
            for fastq in fq2.split(","):
                do_qualitycheck_fastq(fastq, fastqcdir, fastpdir)


def do_mapping(args, samplelist, post, build, chdir):
    if args.nompbl:
#        param_churros_mapping = "-D " + chdir + " -k " + str(args.k) + " -p " + str(args.threads) + " -n"
        param_churros_mapping = f"-D {chdir} -k {args.k} -p {args.threads} -n"
    else:
#        param_churros_mapping = "-D " + chdir + " -k " + str(args.k) + " -p " + str(args.threads)
        param_churros_mapping = f"-D {chdir} -k {args.k} -p {args.threads}"

#    print_and_exec_shell('churros_mapping ' + param_churros_mapping + ' exec ' + str(samplelist) + ' ' + build + ' ' + args.Ddir)
    print_and_exec_shell(f'churros_mapping {param_churros_mapping} exec {samplelist} {build} {args.Ddir}')

    # stats
    qcstatsfile = {chdir}/{build}/churros.QCstats.tsv'
#    os.system('churros_mapping ' + param_churros_mapping + ' header > ' + chdir + '/' + build + '/churros.QCstats.tsv')
    os.system(f'churros_mapping {param_churros_mapping} header > {qcstatsfile}')
#    os.system('churros_mapping ' + param_churros_mapping + ' stats ' + str(samplelist) + ' ' + build + ' ' + args.Ddir + ' >> ' + chdir + '/' + build + '/churros.QCstats.tsv')
    os.system(f'churros_mapping {param_churros_mapping} stats {samplelist} {build} {args.Ddir} >> {qcstatsfile}')


def make_samplepairlist_withflen(samplepairlist, post, build, chdir):
    samplepairlist_withflen = chdir + "/churros.samplepairlist.withflen.txt"
    if(os.path.isfile(samplepairlist_withflen)):
        os.remove(samplepairlist_withflen)

    df = pd.read_csv(samplepairlist, sep=",", header=None)
    df.fillna("", inplace=True)
    for index, row in df.iterrows():
        chip  = row[0]
        input = row[1]
        label = row[2]
        mode  = row[3]

        sspstats = pd.read_csv(chdir + '/sspout/' + chip + post + '.stats.txt', sep="\t", header=0)
        flen = int(sspstats["fragment length"])

        with open(samplepairlist_withflen, 'a') as f:
#            print(chip + "," + input + "," + label + "," + mode + "," + str(flen), file=f)
            print(f"{chip},{input},{label},{mode},{flen}", file=f)

    return samplepairlist_withflen

def ask_to_proceed_with_overwrite(filepath):
    """Produces a prompt asking about overwriting a file.

    # Arguments
        filepath: the path to the file to be overwritten.

    # Returns
        True if we can proceed with overwrite, False otherwise.
    """
    get_input = input
    if sys.version_info[:2] <= (2, 7):
        get_input = raw_input
    overwrite = get_input('[WARNING] the output directory "%s" already exists - overwrite? '
                          '[y/n]' % (filepath))
    while overwrite not in ['y', 'n']:
        overwrite = get_input('Enter "y" (overwrite) or "n" (cancel).')
    if overwrite == 'n':
        return False
    return True

def is_exist_input(samplepairlist):
    df = pd.read_csv(samplepairlist, sep=",", header=None)
    df.fillna("", inplace=True)

    nInput = 0
    for index, row in df.iterrows():
        chip  = row[0]
        input = row[1]
        label = row[2]

        if input != "":
            nInput += 1

    if nInput == 0:
        return False
    else:
        return True

def exec_churros(args):
    samplelist = args.samplelist
    samplepairlist = args.samplepairlist
    build = args.build
    Ddir = args.Ddir
    chdir = args.outputdir
    chdir_build = chdir + "/" + build + "/"

    check_file(samplelist)
    check_file(samplepairlist)

    if os.path.isdir(chdir) and args.force != True:
        if ask_to_proceed_with_overwrite(chdir) == False:
            exit()

    # To absolute path
    samplelist = pathlib.Path(samplelist).resolve()
    samplepairlist = pathlib.Path(samplepairlist).resolve()

    mapparam = args.mapparam
    post = get_mapfile_postfix(mapparam)
    gt = Ddir + '/genometable.txt'

    os.makedirs(chdir, exist_ok=True)

    ### FASTQC
    if args.nofastqc == False:
        do_fastqc(chdir_build, build, samplelist)

    ## churros_mapping
    do_mapping(args, samplelist, post, build, chdir)

    ## make samplepairlist_withflen
    samplepairlist_withflen = make_samplepairlist_withflen(samplepairlist, post, build, chdir_build)

    ## churros_callpeak
    param_macs=' -b bam -p ' + str(args.threads) + ' -q ' + str(args.qval) + ' -d ' + args.macsdir + ' -D ' + chdir
    if os.path.isfile(samplepairlist_withflen):
        print_and_exec_shell('churros_callpeak' + param_macs + ' ' + samplepairlist_withflen + ' ' + build)
    else:
        print_and_exec_shell('churros_callpeak' + param_macs + ' ' + samplepairlist + ' ' + build)

    ## QC check
    print ("\nCheck the quality of ChIP-seq samples...")
    print_and_exec_shell(f'checkQC.py {chdir}/{build}/churros.QCstats.tsv {samplepairlist} | tee {chdir}/{build}/QCcheck.log')

    ### MultiQC
    print_and_exec_shell('multiqc -m fastqc -m fastp -m bowtie2 -m macs2 -f -o ' + chdir_build + ' ' + chdir_build)

    ### generate P-value bedGraph
    if args.outputpvalue:
        if args.nompbl:
            param_churros_genwig = " -n -D" + chdir + " "
        else:
            param_churros_genwig = " -D " + chdir + " "

        print ("\ngenerate Pvalue bedGraph file...")
        print_and_exec_shell('churros_genPvalwig ' + param_churros_genwig + str(samplepairlist) + ' bedGraph_Pval ' + build + ' ' + gt)

    ### make corremation heatmap
    if args.comparative:
        if args.nompbl:
            param_churros_compare = "-n -D" + chdir + " -p " + str(args.threads_comparative) + " "
        else:
            param_churros_compare = " -D " + chdir + " -p " + str(args.threads_comparative) + " "

        print_and_exec_shell('churros_compare ' + param_churros_compare + ' ' + str(samplelist) + ' ' + str(samplepairlist) + ' ' + build)

    ### make pdf files
    print ("\ngenerate pdf files by drompa+...")

    if args.nompbl:
        param_churros_visualize = "-D " + chdir + " --nompbl"
    else:
        param_churros_visualize = "-D " + chdir
    if args.preset == "T2T":
        param_churros_visualize += " --preset T2T "

    if args.preset == "scer":
#        print_and_exec_shell('churros_visualize '+ param_churros_visualize + ' --preset scer --enrich ' + str(samplepairlist) + ' drompa+.macspeak ' + build + ' ' + Ddir)
        print_and_exec_shell(f'churros_visualize {param_churros_visualize} --preset scer --enrich {samplepairlist} drompa+.macspeak {build} {Ddir}')
#        print_and_exec_shell('churros_visualize '+ param_churros_visualize + ' --preset scer --enrich --logratio ' + str(samplepairlist) + ' drompa+.macspeak ' + build + ' ' + Ddir)
        print_and_exec_shell(f'churros_visualize {param_churros_visualize} --preset scer --enrich --logratio {samplepairlist} drompa+.macspeak {build} {Ddir}')

    else:
        df = pd.read_csv(samplepairlist, sep=",", header=None)
        df.fillna("", inplace=True)

        if is_exist_input(samplepairlist):
#            print_and_exec_shell('churros_visualize '+ param_churros_visualize + ' -b 5000 -l 8000 --pvalue -P "--pthre_enrich 3 --scale_pvalue 3" ' + str(samplepairlist) + ' drompa+.pval.bin5M ' + build + ' ' + Ddir)
            print_and_exec_shell(f'churros_visualize {param_churros_visualize} -b 5000 -l 8000 --pvalue -P "--pthre_enrich 3 --scale_pvalue 3" {samplepairlist} drompa+.pval.bin5M {build} {Ddir}')

#            print_and_exec_shell('churros_visualize '+ param_churros_visualize + ' -G ' + str(samplepairlist) + ' ' + 'drompa+ ' + build + ' ' + Ddir)
            print_and_exec_shell(f'churros_visualize {param_churros_visualize} -G {samplepairlist} drompa+ {build} {Ddir}')


#        print_and_exec_shell('churros_visualize '+ param_churros_visualize + ' ' + chdir + '/' + args.macsdir + '/samplepairlist.txt drompa+.macspeak ' + build + ' ' + Ddir)
        print_and_exec_shell(f'churros_visualize {param_churros_visualize} {chdir}/{build}/{args.macsdir}/samplepairlist.txt drompa+.macspeak {build} {Ddir}')

#        print_and_exec_shell('churros_visualize '+ param_churros_visualize + ' -b 5000 -l 8000 -P "--scale_tag 100" ' + str(samplepairlist) + ' drompa+.bin5M ' + build + ' ' + Ddir)
        print_and_exec_shell(f'churros_visualize {param_churros_visualize} -b 5000 -l 8000 -P "--scale_tag 100" {samplepairlist} drompa+.bin5M {build} {Ddir}')



if(__name__ == '__main__'):
    parser = argparse.ArgumentParser()
    parser.add_argument("samplelist", help="sample list", type=str)
    parser.add_argument("samplepairlist", help="ChIP/Input pair list", type=str)
    parser.add_argument("build", help="genome build (e.g., hg38)", type=str)
    parser.add_argument("Ddir", help="directory of reference data", type=str)
    parser.add_argument("--cram", help="output as CRAM format (default: BAM)", action="store_true")
    parser.add_argument("-f", "--force", help="overwrite if the output directory already exists", action="store_true")
    parser.add_argument("-b", "--binsize", help="binsize of parse2wig+ (default: 100)", type=int, default=100)
    parser.add_argument("-k", help="read length for mappability file ([28|36|50], default:50)", type=int, default=50)
    parser.add_argument("--nompbl", help="do not consider genome mappability in drompa+", action="store_true")
    parser.add_argument("--nofastqc", help="omit FASTQC", action="store_true")
    parser.add_argument("-q", "--qval", help="threshould of MACS2 (default: 0.05)", type=float, default=0.05)
    parser.add_argument("--macsdir", help="output direcoty of macs2 (default: 'macs2')", type=str, default="macs")
#    parser.add_argument("-f", "--format", help="output format of parse2wig+ 0: compressed wig (.wig.gz)\n 1: uncompressed wig (.wig)\n 2: bedGraph (.bedGraph) \n 3 (default): bigWig (.bw)", type=int, default=3)
    parser.add_argument("--mapparam", help="parameter of bowtie|bowtie2 (shouled be quated)", type=str, default="")
    parser.add_argument("-p", "--threads", help="number of CPUs (default: 12)", type=int, default=12)
    parser.add_argument("--threads_comparative", help="number of CPUs for --comparative option (default: 8)", type=int, default=8)
    parser.add_argument("--outputpvalue", help="output ChIP/Input -log(p) distribution as a begraph format", action="store_true")
    parser.add_argument("--comparative", help="compare bigWigs and peaks among samples by churros_compare", action="store_true")
    parser.add_argument("-D", "--outputdir", help="output directory (default: 'Churros_result')", type=str, default="Churros_result")
    parser.add_argument("--preset", help="Preset parameters for mapping reads ([scer|T2T])", type=str, default="")
    parser.add_argument("-v", "--version", help="print version information and quit", action='version', version=__version__)

    args = parser.parse_args()
    #    print(args)

    if args.preset != "":
        if args.preset != "scer" and args.preset != "T2T":
            print ("Error: specify [scer|T2T] for --preset option.")
            exit()

    exec_churros(args)
    print ("churros finished.")
