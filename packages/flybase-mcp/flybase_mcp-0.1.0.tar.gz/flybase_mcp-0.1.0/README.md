# FlyBase MCP
MCP server for FlyBase integration

This MCP server allows accessing and retrieving information from FlyBase, a comprehensive database for the genetics and molecular biology of *Drosophila melanogaster*.

## Installation




## Features
* Retrieving a concise summary for a specific gene from FlyBase using its unique gene ID.
* Fetching Gene Ontology (GO) slim terms for a gene by specifying the GO domain, such as `biological_process`, `cellular_component`, or `molecular_function`.


## API reference
### Tools
1. `get_flybase_gene_summary`
   * This tool retrieves a concise summary for a specific gene from FlyBase.
   * Requires: the unique FlyBase gene ID (e.g., FBgn0003362).

2. `get_flybase_gene_ontology`
   * This tool fetches Gene Ontology (GO) slim terms for a gene, categorized by a specific GO domain.
   * Requires: the unique FlyBase gene ID (e.g., FBgn0003362).
     * gene_ontology_domain (str): The specific GO domain to query.

        * Available values for GO: biological_process, cellular_component, molecular_function





