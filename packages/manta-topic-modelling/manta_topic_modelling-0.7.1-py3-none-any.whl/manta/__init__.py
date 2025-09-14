"""
MANTA (Multi-lingual Advanced NMF-based Topic Analysis) - A comprehensive topic modeling library for Turkish and English texts.

This package provides Non-negative Matrix Factorization (NMF) based topic modeling
capabilities with support for both Turkish and English languages. It includes
advanced text preprocessing, multiple tokenization strategies, and comprehensive
visualization and export features.

Main Features:
- Support for Turkish and English text processing
- Multiple NMF algorithm variants (standard NMF and orthogonal projective NMF)
- Advanced tokenization (BPE, WordPiece for Turkish; traditional for English)
- Comprehensive text preprocessing and cleaning
- Word cloud generation and topic visualization
- Excel export and database storage
- Coherence score calculation for model evaluation

Example Usage:
    >>> from manta import run_topic_analysis
    >>> result = run_topic_analysis(
    ...     "data.csv", 
    ...     column="text", 
    ...     language="TR", 
    ...     topics=5
    ... )
    >>> print(f"Found {len(result['topic_word_scores'])} topics")

Command Line Usage:
    $ manta analyze data.csv --column text --language TR --topics 5 --wordclouds
"""

# Version information
__version__ = "0.7.1"
__author__ = "Emir Kyz"
__email__ = "emirkyzmain@gmail.com"

# Lazy import for EmojiMap to keep it in public API while hiding internal modules
def __getattr__(name):
    """Lazy import for public API components."""
    if name == "EmojiMap":
        from ._functions.common_language.emoji_processor import EmojiMap
        return EmojiMap
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

# Public API exports
__all__ = [
    # Main functions
    "run_topic_analysis",
    # Version info
    "__version__",
    "__author__",
    "__email__",
]


def run_topic_analysis(
    filepath: str,
    column: str, 
    separator: str = ",",
    language: str = "EN",
    topic_count: int = 5,
    nmf_method: str = "nmf",
    lemmatize: bool = False,
    tokenizer_type: str = "bpe",
    words_per_topic: int = 15,
    word_pairs_out: bool = True,
    generate_wordclouds: bool = True,
    export_excel: bool = True,
    topic_distribution: bool = True,
    filter_app: bool = False,
    data_filter_options: dict = None,
    emoji_map: bool = False,
    output_name: str = None,
    save_to_db: bool = False,
    output_dir: str = None,
) -> dict:
    """
    Perform comprehensive topic modeling analysis on text data using Non-negative Matrix Factorization (NMF).
    
    This high-level API provides an easy-to-use interface for topic modeling with sensible defaults.
    It supports both Turkish and English languages with various preprocessing and output options.
    
    Parameters:
        filepath: Absolute path to the input file (CSV or Excel format)
        column: Name of the column containing text data to analyze
        separator: CSV file separator (default: ",")
        language: Language of text data - "TR" for Turkish, "EN" for English (default: "EN")
        topic_count: Number of topics to extract. Defaults to 5 for general use. Set to -1 to auto-select the theoretical maximum number of topics.
        words_per_topic: Number of top words to show per topic (default: 15 for general use.) Use 10-20 for most cases.
        nmf_method: NMF algorithm variant - "nmf", "nmtf", or "pnmf". Defaults to "nmf".
        lemmatize: Apply lemmatization for English text (default: False)
        tokenizer_type: Tokenization method for Turkish - "bpe" or "wordpiece" (default: "bpe")
        word_pairs_out: Create word pairs output (default: True)
        generate_wordclouds: Create word cloud visualizations (default: True)
        export_excel: Export results to Excel format (default: True)
        topic_distribution: Generate topic distribution plots (default: True)
        filter_app: Filter data by application name (default: False)
        data_filter_options: Dictionary containing filter options for data filtering:
            - filter_app_name: Application name to filter by (default: "")
            - filter_app_column: Column name for application filtering
            - filter_app_country: Country code to filter by (default: "")
            - filter_app_country_column: Column name for country filtering
        save_to_db: Whether to persist data to database (default: False)
        emoji_map: Enable emoji processing (default: False)
        output_name: Custom name for output directory (default: auto-generated)
        output_dir: Base directory for outputs. Defaults to current working directory.
    Returns:
        Dict containing:
            - state: "SUCCESS" if completed successfully, "FAILURE" if error occurred
            - message: Descriptive message about the processing outcome 
            - data_name: Name of the processed dataset
            - topic_word_scores: Dictionary mapping topic IDs to word-score pairs
            - topic_doc_scores: Dictionary mapping topic IDs to document-score pairs
            - coherence_scores: Dictionary mapping coherence metrics for each topic
            - topic_dist_img: Matplotlib plt object of topic distribution plot if topic_distribution is True
            - topic_document_counts: Count of documents per topic
            - topic_relationships: Topic-to-topic relationship matrix (only for NMTF method)
    Raises:
        ValueError: For invalid language code or unsupported file format
        FileNotFoundError: If input file path does not exist
        KeyError: If specified column is missing from input data.
    Example:
        >>> # Basic usage for Turkish text
        >>> result = run_topic_analysis(
        ...     "reviews.csv",
        ...     column="review_text",
        ...     language="TR",
        ...     topic_count=5,
        ...     generate_wordclouds=True,
        ...     export_excel=True
        ... )
        >>> # Check results
        >>> print(f"Found {len(result['topic_word_scores'])} topics")
    :note:
        - Creates output directories for storing results and visualizations
        - Automatically handles file preprocessing and data cleaning
        - Supports both CSV (with automatic delimiter detection) and Excel files

    """
    from pathlib import Path
    
    # Import dependencies only when needed
    from .manta_entry import run_manta_process
    from .config import create_config_from_params
    
    # Create configuration object from function parameters
    config = create_config_from_params(
        language=language,
        topic_count=topic_count,
        nmf_method=nmf_method,
        lemmatize=lemmatize,
        tokenizer_type=tokenizer_type,
        words_per_topic=words_per_topic,
        word_pairs_out=word_pairs_out,
        generate_wordclouds=generate_wordclouds,
        export_excel=export_excel,
        topic_distribution=topic_distribution,
        separator=separator,
        filter_app=filter_app,
        data_filter_options=data_filter_options,
        emoji_map=emoji_map,
        save_to_db=save_to_db,
        output_name=output_name
    )

    # Set output name if not provided
    if config.output_name is None:
        config.output_name = config.generate_output_name(filepath)

    # Convert config to run_options format
    run_options = config.to_run_options()
    
    # Run the analysis
    return run_manta_process(
        filepath=str(Path(filepath).resolve()),
        table_name=run_options['output_name'],
        desired_columns=column,
        options=run_options,
        output_base_dir=output_dir
    )