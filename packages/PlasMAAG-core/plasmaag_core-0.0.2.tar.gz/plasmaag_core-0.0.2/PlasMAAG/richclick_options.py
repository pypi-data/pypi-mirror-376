import rich_click as click

# Setting rich options
click.rich_click.OPTION_GROUPS = {
    "PlasMAAG": [
        {
            "name": "Defining input files: One of these options are required",
            "options": ["--reads", "--reads_and_assembly_dir"],
        },
        {
            "name": "Additional required Arguments",
            "options": [
                "--output",
                "--threads",
            ],
            "table_styles": {
                "row_styles": ["yellow", "default", "default", "default"],
            },
        },
        {
            "name": "Other Options",
            "options": [
                "--dryrun",
                "--cli_dryrun",
                "--snakemake_arguments",
                "--setup_env",
                "--genomad_db",
                "--vamb_arguments",
                "--help",
            ],
            "table_styles": {
                "row_styles": ["yellow", "default", "default", "default"],
            },
        },
    ],
}

click.rich_click.USE_RICH_MARKUP = True

# Make both -h and --help available instead of just --help
CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])
