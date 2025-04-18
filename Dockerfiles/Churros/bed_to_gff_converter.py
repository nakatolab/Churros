#!/usr/bin/python
# downloaded from Galaxy (https://github.com/najoshi/ucd-biocore-galaxy/blob/master/tools/filters/bed_to_gff_converter.py)

import sys
assert sys.version_info[:2] >= ( 2, 4 )

def __main__():
    input_name = sys.argv[1]
    output_name = sys.argv[2]
    skipped_lines = 0
    first_skipped_line = 0
    out = open( output_name, 'w' )
#    out.write( "##gff-version 2\n" )
#    out.write( "##bed_to_gff_converter.py\n\n" )
    i = 0
    for i, line in enumerate( file( input_name ) ):
        complete_bed = False
        line = line.rstrip( '\r\n' )
        if line and not line.startswith( '#' ) and not line.startswith( 'track' ) and not line.startswith( 'browser' ):
            try:
                elems = line.split( '\t' )
                if len( elems ) == 12:
                    complete_bed = True
                chrom = elems[0]
                if complete_bed:
                    feature = "mRNA"
                else:
                    try:
                        feature = elems[3]
                    except:
                        feature = 'feature%d' % ( i + 1 )
                start = int( elems[1] ) + 1
                end = int( elems[2] )
                try:
                    score = elems[4]
                except:
                    score = '0'
                try:
                    strand = elems[5]
                except:
                    strand = '+'
                try:
                    group = elems[3]
                except:
                    group = 'group%d' % ( i + 1 )
                if complete_bed:
                    out.write( '%s\t%s\tbed2gff\t%d\t%d\t%s\t%s\t.\t%s %s;\n' % ( chrom, feature, start, end, score, strand, feature, group  ) )
                else:
                    out.write( '%s\t%s\tbed2gff\t%d\t%d\t%s\t%s\t.\t%s;\n' % ( chrom, feature, start, end, score, strand, group  ) )
                if complete_bed:
                    # We have all the info necessary to annotate exons for genes and mRNAs
                    block_count = int( elems[9] )
                    block_sizes = elems[10].split( ',' )
                    block_starts = elems[11].split( ',' )
                    for j in range( block_count ):
                        exon_start = int( start ) + int( block_starts[j] )
                        exon_end = exon_start + int( block_sizes[j] ) - 1
                        out.write( '%s\tbed2gff\texon\t%d\t%d\t%s\t%s\t.\texon %s;\n' % ( chrom, exon_start, exon_end, score, strand, group ) )
            except:
                skipped_lines += 1
                if not first_skipped_line:
                    first_skipped_line = i + 1
        else:
            skipped_lines += 1
            if not first_skipped_line:
                first_skipped_line = i + 1
    out.close()
    info_msg = "%i lines converted to GFF version 2.  " % ( i + 1 - skipped_lines )
    if skipped_lines > 0:
        info_msg += "Skipped %d blank/comment/invalid lines starting with line #%d." %( skipped_lines, first_skipped_line )
    print info_msg

if __name__ == "__main__": __main__()
