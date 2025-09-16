from dataclasses import dataclass, field, make_dataclass
from typing import Optional, ClassVar

header_tuple = (
    "assembly_accession",
    "bioproject",
    "biosample",
    "wgs_master",
    "refseq_category",
    "taxid",
    "species_taxid",
    "organism_name",
    "infraspecific_name",
    "isolate",
    "version_status",
    "assembly_level",
    "release_type",
    "genome_rep",
    "seq_rel_date",
    "asm_name",
    "asm_submitter",
    "gbrs_paired_asm",
    "paired_asm_comp",
    "ftp_path",
    "excluded_from_refseq",
    "relation_to_type_material",
    "asm_not_live_date",
    "assembly_type",
    "group",
    "genome_size",
    "genome_size_ungapped",
    "gc_percent",
    "replicon_count",
    "scaffold_count",
    "contig_count",
    "annotation_provider",
    "annotation_name",
    "annotation_date",
    "total_gene_count",
    "protein_coding_gene_count",
    "non_coding_gene_count",
    "pubmed_id",
)

# Create the dataclass with all fields optional
tableRow = make_dataclass(
    "AssemblySummary",
    [(name, Optional[str], field(default=None)) for name in header_tuple],
    slots=True
)

# Add the class method
@classmethod
def from_list(cls, values):
    if len(values) != len(header_tuple):
        raise ValueError(f"Expected {len(header_tuple)} values, got {len(values)}.")
    return cls(*values)

# Add a cleaner __repr__ method
def __repr__(self):
    col1_width = 20
    return f"{self.assembly_accession.ljust(col1_width)}  {self.ftp_path}"

# Assign the methods to the class
tableRow.from_list = from_list
tableRow.__repr__ = __repr__
