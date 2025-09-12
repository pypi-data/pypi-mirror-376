[![Downloads](https://pepy.tech/badge/sonicparanoid/month)](https://pepy.tech/project/sonicparanoid/month)
[![Latest version](https://img.shields.io/pypi/v/sonicparanoid.svg?label=latest%20version)](https://pypi.org/project/sonicparanoid)
[![Python versions](https://img.shields.io/pypi/pyversions/sonicparanoid.svg)](https://pypi.org/project/sonicparanoid)
![License](https://img.shields.io/pypi/l/sonicparanoid.svg?color=green)

# SonicParanoid
> Fast, accurate, and comprehensive orthology inference with machine learning and language models

## Description

SonicParanoid is a stand-alone software for the identification of orthologous relationships among multiple species. SonicParanoid is an open source software released under the GNU GENERAL PUBLIC LICENSE, Version 3.0 ([GPLv3](https://www.gnu.org/licenses/gpl-3.0.html)), implemented in Python3, Cython, and C++. It works on Linux and Mac OSX.

### Fast and Scalable
SonicParanoid is able to infer the orthologs for hundres of prokaryotes in hours, or days for eukaryotes, using a desktop computer with 8 CPUs. This figure is much smaller when running on HPC servers with dozens of CPUs (e.g. <1h for the [QfO benchmark](https://questfororthologs.org/) datasets).
It is also highly scalable, as it inferred the orthologs for 2000 MAGs in only 1 day using 128 CPUs.

### Fast and scalable domain-aware orthology inference
SonicParanoid uses language models to infer orthologs at the domain level. The Artificial Neural Networks are directly trained on the input proteome set and it show a quasi-linear scalability on the number of input proteomes.

### Accurate
SonicParanoid was tested using a benchmark proteome dataset from the [Quest for Orthologs consortium](https://questfororthologs.org/), and the correctness of its predictions was evaluated using a standardized [Orthology Benchmarking service](https://orthology.benchmarkservice.org).
SonicParanoid showed a balanced trade-off between precision and recall, with an accuracy comparable to those of well-established inference methods.

### Easy to use
Thanks to its speed, accuracy, and usability SonicParanoid substantially relieves the difficulties of orthology inference for biologists who need to construct and maintain their own genomic datasets.

## Installation
>For more detail on how to use and install SonicParanoid go its wiki-page:
> https://gitlab.com/salvo981/sonicparanoid2/-/wikis/home

### Citation
> Salvatore Cosentino, Sira Sriswasdi and Wataru Iwasaki (2024),
> _SonicParanoid2: fast, accurate, and comprehensive orthology inference with machine learning and language models._
> __Genome Biology__. 25, Article number: 195 (2024)
> https://doi.org/10.1186/s13059-024-03298-4
> ![Endpoint Badge](https://img.shields.io/endpoint?url=https%3A%2F%2Fapi.juleskreuer.eu%2Fcitation-badge.php%3Fshield%26doi%3D10.1186%2Fs13059-024-03298-4&style=flat&color=(256%2C%20256%2C%20256))
>
>
> Salvatore Cosentino and Wataru Iwasaki (2019),
> _SonicParanoid: fast, accurate and easy orthology inference._
> __Bioinformatics.__ Volume 35, Issue 1, 1 January 2019, Pages 149–151.
> https://doi.org/10.1093/bioinformatics/bty631
> ![Endpoint Badge](https://img.shields.io/endpoint?url=https%3A%2F%2Fapi.juleskreuer.eu%2Fcitation-badge.php%3Fshield%26doi%3D10.1093%2Fbioinformatics%2Fbty631&style=flat&color=(256%2C%20256%2C%20256))


### Changelog
> For the complete changelog visit the [release page on GitLab](https://gitlab.com/salvo981/sonicparanoid2/-/releases)

#### 2.0.9 (September 2025)

- Python version: 3.10<=python<3.13 (this means that **Python 3.9** is not supported anymore)
- Enhancement: when installing MMseqs, the human-readeable version is also shown together with the hash commit for such version.
- Enhancement: allow [installation using Mamba](https://gitlab.com/salvo981/sonicparanoid2/-/issues/73) (mini-forge)
- Fix: [pip install error](https://gitlab.com/salvo981/sonicparanoid2/-/issues/82) due to obsolete cython code
- Fix: package [conflict when installing using Micromamba](https://gitlab.com/salvo981/sonicparanoid2/-/issues/74)
- Maintenance: upgraded Blast+ to v2.15.0


#### 2.0.8 (August 7, 2024)

- Announcement: [SonicParanoid2 was published](https://doi.org/10.1186/s13059-024-03298-4)!
- Citation links were updated.
- Maintenance: upgrade to latest Diamond version (v2.1.9)
- Fix: Avoid Diamond to fail when proteins containing only bases same as DNA bases are given as input. This is done by adding `--ignore-warnings` to the `makedb` and `blastp` commands.


#### 2.0.7 (June 27, 2024)

- New: Added a new program called [sonicparanoid-get-profiles](https://gitlab.com/salvo981/sonicparanoid2/-/wikis/Install-MMseqs-Pfam-profiles) to download the MMseqs-PFam profile DB files. This can be used if the [Profile DB could not be built locally](https://gitlab.com/salvo981/sonicparanoid2/-/issues/54).
- Maintenance: Upgrade cython code to use `dataclasses` [issue](https://gitlab.com/salvo981/sonicparanoid2/-/issues/68).
- Fix: [scikit-learn issue](https://gitlab.com/salvo981/sonicparanoid2/-/issues/55) and upgrade the dependency to 1.5.0
- Fix: [inclusion of hits with lower bitscores due to overwrite](https://gitlab.com/salvo981/sonicparanoid2/-/issues/63)
- Fix: in species-species ortholog [tables single relations were counted as 2](https://gitlab.com/salvo981/sonicparanoid2/-/issues/69)
- Fix: [slowdowns due to queue timeout](https://gitlab.com/salvo981/sonicparanoid2/-/issues/65) (only happened with thousands of proteomes and using slow storage)
- Python version: 3.9<=python<3.13 (this means that Python 3.8 is not supported anymore)
- Maintenance: update to support the latest Cython release
- Maintenance: include early version of pyproject.toml (still use setup.py to compile Cython source files)

#### 2.0.5 (April 9, 2024)
- Fix: Scipy version related issue [issue](https://gitlab.com/salvo981/sonicparanoid2/-/issues/66).
- New feature: [as requested](https://gitlab.com/salvo981/sonicparanoid2/-/issues/60), it is now possible extract multi-fasta files for selected (or all) output OGs.
- Fix: [issue](https://gitlab.com/salvo981/sonicparanoid2/-/issues/57) that caused errors using some `ANACONDA` installations.

#### 2.0.4 (July 3, 2023)
Maintenance update.
- Fix: [issue](https://gitlab.com/salvo981/sonicparanoid2/-/issues/55) that caused SP2 to fail to predict the fastest alignments when using `scikit-learn v1.3.0 and above`.
- Others: The installation guides in the web-page were updated to reflect the above fixed issue.

#### 2.0.3 (June 6, 2023)
Small but important bug-fixes.
- Fix: [issue](https://gitlab.com/salvo981/sonicparanoid2/-/issues/50) that caused the domain-based orthology to fail when processing huge proteomes.
- Fix: [error](https://gitlab.com/salvo981/sonicparanoid2/-/issues/49) during creation of the PfamA profile DB.
- Others: updated information on how to cite SP2.

#### 2.0.2 (May 28, 2023)
This is a small maintenance update.
- New: Support installation using [Mamba/micromamba environments](https://github.com/mamba-org).
- Fixed an [error](https://github.com/hashdist/hashdist/issues/113) caused by `shutil.rmtree` on NFS file systems.

#### 2.0.1 (May 2, 2023)
This is a massive update which introduces a lot new and features and improvements.
`SonicParanoid2` uses machine leaning for faster orthology and more comprehensive ortholgy inference.
Visit the [web-page](http://iwasakilab.k.u-tokyo.ac.jp/sonicparanoid/) for more details.
- New: reduced all-vs-all execution time for all-vs-all alignments by 20~50% (depending on the dataset).
- New: domain-aware orthology inference
- Enhancement: you can now see the state of your run in real-time through status bars
- Breaking change: many parameters have removed/added check the web-page more details.
- Breaking change: removed single-linkage clustering for OGs
- Python version: 3.8<=python<=3.10

#### 1.3.8 (November 10, 2021)
- Summary: fixed some important issues related to `Diamond` introduced with version `v1.3.7`.
- Hot-fix: [Missing otholog table](https://gitlab.com/salvo981/sonicparanoid2/-/issues/37).
- Hot-fix: Error when using [Diamond and index files](https://gitlab.com/salvo981/sonicparanoid2/-/issues/38).
- Others: The minimum required memory per thread was reduced to `1 GigaByte`.

#### 1.3.7 (November 8, 2021)
- Maintenance: upgraded to [Diamond (v2.0.12)](https://github.com/bbuchfink/diamond/releases/tag/v2.0.12)
- Breaking change: the ortholog tables do not have their own directory anymore. For example for species 1 and 2 the ortholog table will stored under `/project/orthologs_db/1/table.1-2`
- Breaking change: the ortholog matrixes are now stored under the directory '/project/ortholog_matrixes/'
- Enhancement: more [efficient directory structure](https://gitlab.com/salvo981/sonicparanoid2/-/issues/35) for the `orthologs_db` directory.
- Fix: [Inconsistent OG counts](https://gitlab.com/salvo981/sonicparanoid2/-/issues/36) with the same input dataset.
- Others: set default value for the `--max-len-diff` parameter to `0.75`.

#### 1.3.6 (September 17, 2021)
- Feature: [BLAST](https://blast.ncbi.nlm.nih.gov/Blast.cgi) can now be selected using the parameter `--aln-tool`
- Feature: [Diamond (v2.0.11)](https://github.com/bbuchfink/diamond/releases/tag/v2.0.9) can now be selected using the parameter `--aln-tool`
- Feature: added parameter `--min-bitscore` to set minimum bitscore for all-vs-all alignments (default is 40)
- Usability: `ANACONDA` should now be used for installation on MacOS (and Linux were needed). Check the web-page for more details
- Enhancement: added support for Python 3.9
- Enhancement: retrained Adaboost model with new training data
- Maintenance: upgraded to [MMseqs2 version 13-45111](https://github.com/soedinglab/MMseqs2/releases/tag/13-45111)
- Fix: [Throw an ERROR when empty files are input](https://gitlab.com/salvo981/sonicparanoid2/-/issues/33)
- Fix: [Wrong automatic project naming](https://gitlab.com/salvo981/sonicparanoid2/-/issues/30)
- Breaking change: binaries (e.g., of MMSeqs) are now inside a single directory called `software_packages`
- Breaking change: the `-ml` parameter is set to 1 by default
- Breaking change: single linkage clustering was removed. The `-slc` parameter was accordingly removed
- Breaking change: the parameter `--max-gene-per-sp` was removed
- Others: minimum coverages for orthologs set to 20% and 20%

#### 1.3.5 (December 11, 2020)
- Enhancement: by default alignments are now compressed using the [DEFLATE](https://en.wikipedia.org/wiki/DEFLATE) method in order to save storage space. The default compression level is 5 but it can be changed using the `--compression-lev` parameter.
- Enhancement: reduces the I/O operations.
- Usability: Added guide for the installation using [CONDA](https://www.anaconda.com/) to the [web-page](http://iwasakilab.bs.s.u-tokyo.ac.jp/sonicparanoid/)
- Usability: removed [homebrew](https://brew.sh/) as a requirement on MacOS
- Usability: general improvements to the [web-page](http://iwasakilab.bs.s.u-tokyo.ac.jp/sonicparanoid/)
- Maintenance: added [filetype](https://pypi.org/project/filetype/) as a dependency
- Fix: [Execution error when using python 3.6](https://gitlab.com/salvo981/sonicparanoid2/-/issues/22)

#### 1.3.4 (July 25, 2020)
- Enhancement: execution is 5~10% faster when many small proteomes are given input (e.g. > 1000)
- Enhancement: considerably reduced IO when generating the alignments
- Enhancement: when the available CPUs are more than the required alignment jobs these will be equally split between jobs instead of using 1 thread per job. This considerably reduces execution times when few big proteomes are in input, and many threads are available.
- Enhancement: more informative output from the command line
- Enhancement: output directories are now easier to browse even when many input files are provided
- Enhancement: MCL binaries automatically installed for Linux and MacOS
- Enhancement: warnings are shown only in debug mode
- Enhancement: avoid users to restart a run using a different MMseqs sensitivity
- Enhancement: automatically remove incomplete alignments when restarting a run
- Maintenance: added `wheel` as a dependency and removed `sh`
- Maintenance: upgraded to [MMseqs2 version 11-e1a1c](https://github.com/soedinglab/MMseqs2/releases/tag/11-e1a1c)
- Fix: [Inconsistent results when using non-indexed target databases](Https://gitlab.com/salvo981/sonicparanoid2/-/issues/18). Big thanks to [Keito](https://twitter.com/watano_k10) for providing the dataset.
- Fix: [wrongly formatted execution times](https://gitlab.com/salvo981/sonicparanoid2/-/issues/19) in the alignments stats file.
- Breaking change: alignments and ortholog tables are now organized into subdirectories, please check the [web-page](http://iwasakilab.bs.s.u-tokyo.ac.jp/sonicparanoid/) for details

#### 1.3.2 (April 23, 2020)
- Enhancement: Added support for Python 3.8
- Maintenance: Increased minimum version for packages, Cython(0.29); pandas(1.0); numpy(1.18); scikit-learn(0.22); scipy(1.2.1); mypy(0.720); biopython(1.73)
- Maintenance: Retrained prediction models using the latest version scikit-learn (0.22)
- Fix: [Too many open files error](https://gitlab.com/salvo981/sonicparanoid2/-/issues/15). Big thanks to [Eva Deutekom](https://twitter.com/EvanderDeut)
- Fix: [Removed scikit-lean warnings](https://gitlab.com/salvo981/sonicparanoid2/-/issues/10)

#### 1.3.0 (November 26, 2019)
- Enhancement: SonicParanoid is much faster when using high sensitivity modes! Check the [web-page](http://iwasakilab.bs.s.u-tokyo.ac.jp/sonicparanoid/#extimes)
- Enhancement: run directory names embed information about the run settings
- Enhancement: generated temporary files are much smaller now
- Fix: [error with only 2 input species](https://gitlab.com/salvo981/sonicparanoid2/issues/9). Big thanks to [Benjamin Hume](https://scholar.google.co.jp/citations?hl=en&user=gZj6l8sAAAAJ)
- Fix: force overwriting of MMseqs2 binaries if the version is different from the supported one
- Usability: Tested on Arch-based [Manjaro Linux](https://manjaro.org)
- Others: Big thanks to [Shun Yamanouchi](https://twitter.com/Mt_Nuc) for providing some challenging datasets used for testing
- Maintenance: upgraded to [MMseqs2 version 10-6d92c](https://github.com/soedinglab/MMseqs2/releases/tag/10-6d92c)

#### 1.2.6 (August 26, 2019)
- Fix: `to many files open` error which sometimes happened when using more than 20 threads

#### 1.2.5 (August 7, 2019)
- Fix: Logical threads are considered instead of physical cores in the adjustment of the threads number
- Requirements: a minimum of 1.75 gigabytes per thread is required (the number of threads is automatically adjusted)
- Enhancement: added parameter `--force-all-threads` to bypass the check for minimum per-thread memory

#### 1.2.4 (July 14, 2019)
- Enhancement: Added control to avoid selecting a number threads higher than the available physical CPU cores (big thanks to [Shun Yamanouchi](https://twitter.com/Mt_Nuc))
- Fix: Removed some scipy warnings, now shown only in debug mode (thanks to [Alexie Papanicolaou](https://gitlab.com/alpapan))
- Requirements: [psutils](https://pypi.org/project/psutil/)>=5.6.0 is now required
- Requirements: [mypy](https://pypi.org/project/mypy/)>=0.701 is now required
- Requirements: at least Python 3.6 is now required

#### 1.2.3 (June 7, 2019)
- Enhancement: some error messages are more informative (big thanks to [Jeff Stein](https://gitlab.com/jvstein))

#### 1.2.2 (May 13, 2019)
- Fix: solved a bug that caused MCL to be not properly compiled on some Linux distributions
- Info: source code migrated to [GitLab](https://gitlab.com/salvo981/sonicparanoid2)

#### 1.2.1 (May 10, 2019)
- Fix: solved bug related to random missing alignments
- Info: this issue was first described in [here](https://bitbucket.org/salvocos/sonicparanoid/issues/2/two-problems-with-qfo2011)

#### 1.2.0 (April 26, 2019)
- Change: Markov Clustering (MCL) is now used by default for the creation of ortholog groups
- Enhancement: the MCL inflation can be controlled through the parameter `--inflation`
- Enhancement: Output file with single-copy ortholog groups
- Feature: single-linkage clustering for ortholog groups creation through the `--single-linkage` parameter
- Enhancement: added secondary program to filter ortholog groups
- Info: type `sonicparanoid-extract --help` to see the list of options
- Enhancement: Filter ortholog groups by species ID
- Enhancement: Filter ortholog groups by species composition (e.g. only groups with a given number of species)
- Enhancement: Extract FASTA sequences of orthologs in selected groups
- Fix: The correct version of SonicParanoid is now shown in the help
- Others: General bug fixes and under-the-hood improvements

#### 1.1.2 (March, 2019)
- Enhancement: Filter ortholog groups by species ID
- Enhancement: Filter ortholog groups by species composition (e.g. only groups with a given number of species)
- Enhancement: Extract FASTA files corresponding orthologs in selected groups
- Fix: The correct version of SonicParanoid is now shown in the help

#### 1.1.1 (January 24, 2019)
- Enhancement: No restriction on file names
- Enhancement: No restriction on symbols used in FASTA headers
- Enhancement: Added file with genes that could not be inserted in any group (not orthologs)
- Enhancement: Added some statistics on the predicted ortholog groups
- Enhancement: Update runs are automatically detected
- Enhancement: Improved inference of in-paralogs
- Enhancement: The directory structure has been redesigned to better support run updated

#### 1.0.14 (October 19, 2018)
- Enhancement: a warning is shown if non-protein sequences are given in input
- Enhancement: upgraded to MMseqs2 6-f5a1c
- Enhancement: SonicParanoid is now available through [Bioconda](https://bioconda.github.io/recipes/sonicparanoid/README.html)

#### 1.0.13 (September 18, 2018)
- Fix: allow FASTA headers containing the '@' symbol

#### 1.0.12 (September 7, 2018)
- Improved accuracy
- Added new sensitivity mode (most-sensitive)
- Fix: internal input directory is wiped at every new run
- Fix: available disk space calculation

#### 1.0.11 (August 7, 2018)
- Added new program (sonicparanoid-extract) to process output multi-species clusters
- Added the possibility to analyse only 2 proteomes
- Added support for Python3.7
- Python3 versions: 3.5, 3.6, 3.7
- Upgraded MMseqs2 (commit: a856ce, August 6, 2018)

#### 1.0.9 (May 10, 2018)
- First public release
- Python3 versions: 3.4, 3.5, 3.6
