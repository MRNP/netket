"""
usage: doc_diff.py [DocPath1 DocPath2 ...]

DocPath1, ...   List the directories to perform consistency check of
                documentation for (optional).

This test reads in all previously generated NetKet documentation and compares it
to the documentation generated by calling `make_class_docs`. This test will fail
if there is a mismatch in any document (returns non-zero error code). 

The purpose of the test is to make sure that any updates to the documentation
generating tools do not cause unwanted modifications. 

How to use this test:

1. Re-generate the documentation to make sure that it is up to date.
2. Apply the update patch to the documentation tools.
3. Run this test.

Example output:
 python3 doc_diff.py Graph
 Building documentation for: netket.graph.Hypercube
 Mismatch found in: netket.graph.Hypercube
 Report written to: reports/graph/Hypercube.html
 Building documentation for: netket.graph.CustomGraph
 Mismatch found in: netket.graph.CustomGraph
 Report written to: reports/graph/CustomGraph.html

"""

import filecmp
import difflib
import os
import sys
import format as fmt
import netket
import shutil

build_dir = 'temp'
report_dir = 'report'

# this list will be overwritten if command line arguments are passed.
doc_dirs = ['Graph']

def get_generated_docs():
    """
    Return a list of paths to generated docs (e.g., `Graph/Hypercube.md`), paths
    to docs to generate, and module import statement (e.g., `graph.hypercube`). 

    """
    # Reference files
    ref_files = []
    # Potentially modified files (these are temporarily written to disk)
    mod_files = []
    # Module import statements
    classes = []
    for doc_dir in doc_dirs:
        tmp = os.listdir(doc_dir)
        for file_ in tmp:
            ref_files.append('%s/%s'%(doc_dir, file_))
            mod_files.append('%s/%s/%s'%(build_dir, doc_dir, file_))
            classes.append('netket.%s.%s'%(doc_dir.lower(),
                           file_.split('.')[0])) 

    return ref_files, mod_files, classes

def init_dir(new_dir):
    if not os.path.isdir(new_dir):
        os.mkdir(new_dir)

def build(class_name, output_name, verbose=1):
    """
    Temporarily build the documentation.
    """
    if verbose:
        print("Building documentation for: %s"% class_name)  
    class_obj = eval(class_name)
    markdown = fmt.format_class(class_obj)

    with open(output_name, 'w') as filehandle:
        filehandle.write(markdown)


def make_report(ref_file, mod_file, class_name, report_dir='reports/',
                verbose=1):
    """
    Compare previously generated docs with most recent version. Generate a HTML
    report for any files that do not match. 

    Args:
        ref_file: path to reference file.
        mod_file: path to modified file.

    Returns:
        A flag that is set to `True` if any inconsistencies are encountered.

    """
    is_consistent = filecmp.cmp(ref_file, mod_file)

    if not is_consistent:
        init_dir(report_dir)
        fromlines = open(ref_file).read().split('\n')
        tolines = open(mod_file).read().split('\n')
        report = difflib.HtmlDiff()
        html = report.make_file(fromlines, tolines)
        # remove netket from path
        out_file = '%s/%s'%(report_dir, 
                           '/'.join(class_name.replace('.',
                           '/').split('/')[1::]))
        out_dir = os.path.dirname(out_file)

        print("Mismatch found in: %s"%class_name)
        init_dir(out_dir)
        with open(out_file + '.html', 'w') as filehandle:
            filehandle.write(html)

        if verbose:
            print("Report written to: %s.html"%out_file)

    return is_consistent

def init_docs(build_dir, doc_dirs):
    init_dir(build_dir)
    for doc_dir in doc_dirs:
        init_dir('%s/%s'%(build_dir, doc_dir))

def run(build_dir, doc_dirs, report_dir):
    init_docs(build_dir, doc_dirs)
    ref_files, mod_files, classes = get_generated_docs()
    err = False
    for ref_file, mod_file, class_name in zip(ref_files, mod_files, classes):
        build(class_name, mod_file)
        is_consistent = make_report(ref_file, mod_file, class_name, report_dir)
        if not is_consistent:
            err = True

    # Remove directory that contains temporarily generated docs. 
    shutil.rmtree(build_dir)

    return err

if len(sys.argv) > 1:
    doc_dirs = sys.argv[1::]

sys.exit(run(build_dir, doc_dirs, report_dir))