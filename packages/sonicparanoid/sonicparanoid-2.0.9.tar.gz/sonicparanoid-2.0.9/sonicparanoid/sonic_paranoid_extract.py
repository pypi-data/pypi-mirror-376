# -*- coding: utf-8 -*-
'''Extract clusters from SonicParanoid's output.'''
import os
import sys
from typing import Any
#### IMPORT TO GENERATE PyPi package
#'''
from sonicparanoid import process_output as po
#'''
####



########### FUNCTIONS ############
def get_params() -> Any:
    """Parse and analyse command line parameters."""
    # define the parameter list
    import argparse
    parser = argparse.ArgumentParser(description='SonicParanoid-extract {:s}'.format(po.__version__),  usage='%(prog)s -i <input-table> [options]', prog='sonicparanoid-extract')
    #start adding the command line options
    parser.add_argument('-i', '--input-table', type=str, required=True, help='Table with ortholog groups generated using SonicParanoid. NOTE: the headers must not be modified not removed.', default=None)
    parser.add_argument('-o', '--output-directory', type=str, required=True, help='Directory in which the results will be stored.', default='')
    parser.add_argument('-fd', '--fasta-directory', type=str, required=False, help='Directory containing the original input proteome files in FASTA format.', default='')
    parser.add_argument('-minsp', '--min-sp', type=int, required=False, help='Extract ortholog groups with genes from at least --min-sp species. (Default=2)', default=0)
    parser.add_argument('-maxsp', '--max-sp', type=int, required=False, help='Extract ortholog group with genes from at max --max-sp species. (Default=2)', default=0)
    parser.add_argument('-ids','--ids-list', type=str, required=False, help='Extract a list of ortholog groups by their ids.\nNOTE: the ids should be separated by a comma (e.g., --ids-list 20,23,40,22); this parameter bypasses the --min-sp and max-sp.', default='')
    # minConfDefault: float = 0.05
    # parser.add_argument('-c', '--min-conf', type=float, required=False, help='Keep only orthologs with a confidence higher than --min-conf. (Default={:.2f})'.format(minConfDefault), default=minConfDefault)
    parser.add_argument('-f', '--fasta', required=False, help='Generate a FASTA file with the proteins in each selected ortholog group.', default=False, action='store_true')
    parser.add_argument('-mf', '--multiple-fasta', required=False, help='Generate a FASTA file for each species in each ortholog group. (implies --fasta)', default=False, action='store_true')
    parser.add_argument('--single-copy-only', required=False, help='Consider only single copy clusters.', default=False, action='store_true')
    parser.add_argument('-ac','--annot-cols', type=str, required=False, help='Column ids containing annotations for the new HDR.\nNOTE: the column positions should be separated by a comma (e.g., --annot-cols 1,2,4,5); this parameter bypasses.', default='')
    parser.add_argument('-af', '--annot-file', type=str, required=False, help='Table with tab-serataed fields with annotations.', default=None)
    parser.add_argument('-gci', '--gene-col-id', type=int, required=False, help='Column number of the annotation file containing the protein id.', default=-1)
    parser.add_argument('-d', '--debug', required=False, help='Output debug information.', default=False, action='store_true')
    # return list with params
    return parser.parse_args()



########### MAIN ############
def main() -> None:

    #Get the parameters
    args = get_params()
    #start setting the needed variables
    debug: bool = args.debug
    inTbl: str = args.input_table
    inDir: str = ""
    outDir: str = ""
    if args.input_table is not None:
        inDir = os.path.realpath(args.input_table)
    if len(args.output_directory) > 0:
        outDir = os.path.realpath(args.output_directory)
    else:
        outDir = os.getcwd()

    # extract fasta
    getFasta: bool = args.fasta
    multiFasta: bool = args.multiple_fasta
    singleCopyOnly: bool = args.single_copy_only
    if multiFasta: # force getFasta to True
        getFasta = True
    # make sure the directory with proteomes exists
    fastaDir: str = ""
    if getFasta:
        if len(args.fasta_directory) == 0:
            sys.stderr.write('\nERROR: you must specify the path to the directory containing the original FASTA files for the analyzed species.\nUse the -fd/--fasta-directory parameter.\n')
            sys.exit(-5)
        else:
            fastaDir = os.path.realpath(args.fasta_directory)
    

    # set flag control the type of extraction
    byId: bool = True
    # extract min and max sp count
    minSp: int = args.min_sp
    maxSp: int = args.max_sp

    # extract the list of ids
    idsListRaw: str = args.ids_list
    idsList: list[str] = idsListRaw.strip(' ').split(',')
    print(idsList)

    # remove any empty entry
    idx: int = -1
    while True:
        try:
            idx = idsList.index('')
            del idsList[idx]
        except ValueError:
            idx = -1
            break
    # remove repeated entries if any
    tmpDict = {x:None for x in idsList}
    idsList = list(tmpDict.keys())
    del tmpDict

    # count the number of species in the table
    ifd = open(inTbl, "rt")
    spCnt = int(len(ifd.readline().split("\t")) - 4)

    if minSp + maxSp >= 2: # at least one of the 2 values has been set
        if len(idsList) == 0:
            byId = False
            # adjust the min and max values if required
            if minSp < 2:
                minSp = 2
            if maxSp < 2:
                maxSp = spCnt
        else:
            print("ERROR: it is not possible to use the extraction by ID (--ids-list) and by species composition (--maxsp and/or --minsp) at the same time.")
            sys.exit(-6)

    # now check the parameters regarding the annotation
    # flag that says if annotation should be performed
    annotate: bool = False

    # make sure the annotation file exists
    annotPath: str
    if args.annot_file:
        annotPath = os.path.realpath(args.annot_file)
        if not os.path.isfile(annotPath):
            sys.stderr.write('\nERROR: you must specify the path to the file containing the annotations.\n')
            sys.exit(-2)
        else:
            annotate = True

    # now check the annot-cols parameter
    # extract the list of ids
    colsListRaw: str = args.annot_cols
    colsList: list[str] = colsListRaw.strip(' ').split(',')

    # remove any empty entry
    idx = -1
    while True:
        try:
            idx = colsList.index('')
            del colsList[idx]
        except ValueError:
            idx = -1
            break

    # convert column ids to integers
    tmpColsList: list[int] = [int(x) for x in colsList]
    del colsList
    colsListInt: list[int] = tmpColsList
    del tmpColsList

    # check congruency of annot-cols other annotation related parameters
    if len(colsListInt) == 0:
            if annotate: # then no annotation column was provided
                sys.stderr.write('\nERROR: you must specify the position of at least one column in the annotation file\n{:s}\n'.format(annotPath))
                sys.exit(-5)
    else:
        if not annotate: # the annotation file was not specified
            sys.stderr.write('\nERROR: you must specify the path to the annotation file.\n')
            sys.exit(-5)

    # now check the gene-col-id parameter
    geneColId: int = args.gene_col_id
    if geneColId >= 0:
        if annotate:
            # make sure that the annotation column list does not contain only the gene-col-id
            if len(colsListInt) == 1:
                if colsListInt[0] == geneColId:
                    sys.stderr.write('\nERROR: the annotation column position must differ from the gene ID column position.\n')
                    sys.exit(-5)
    elif geneColId < 0: # This would not fail if genColId == -1
        if annotate:
            sys.stderr.write('\nERROR: you must specify an interger higher than 0 as the column position with the gene IDs in the annotation file.\n')
            sys.exit(-5)

    #if debug:
    print("\nSonicParanoid-extract will be executed with the following parameters:")
    print(f"Input ortholog groups table: {inTbl}")
    print(f"Species in the ortholog groups table: {spCnt:d}")
    print(f"Consider only single copy orthologs:\t{singleCopyOnly}")
    print(f"Output directory: {outDir}")
    # print('Minimum ortholog confidence:\t{:.2f}'.format(minConf))
    if getFasta:
        print(f"Directory with the analyzed FASTA files: {fastaDir}")
    if byId:
        print(f"Clusters to be extracted:\t{idsList}")

    # define stats output file
    statsPath: str = os.path.join(outDir, 'stats.tsv')
    # write stats about the groups table
    po.process_multisp_tbl(inTbl=inTbl, outPath=statsPath, debug=debug)

    # perform the extraction
    clstrDict: dict[str, dict[str, list[str]]] = {}
    if byId:
        clstrDict = po.extract_by_id(inTbl=inTbl, idList=idsList, outDir=outDir, minConf=0.1, singleCopyOnly=singleCopyOnly, debug=debug)
    else:
        clstrDict = po.extract_by_sp_cnt(inTbl=inTbl, min=minSp, max=maxSp, outDir=outDir, minConf=0.1, singleCopyOnly=singleCopyOnly, debug=debug)
    
    # extract the fasta sequence if required
    if getFasta:
        # check if the annotation should be included in the headers
        annotDict: dict[str, list[list[str]]] = {}
        if annotate:
            annotDict = po.load_annotations(annotFile=annotPath,  geneIdCol=geneColId, annotCols=colsListInt, debug=debug)
            #sys.exit('DEBUG :: sonic_paranoid_extract')
        po.extract_fasta(clstrDict=clstrDict, fastaDir=fastaDir, outDir=outDir, multiFasta=multiFasta, annotationDict=annotDict, debug=debug)

    # sys.exit("DEBUG")

if __name__ == "__main__":
    main()
