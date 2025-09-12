from pydantic import BaseModel, Field


class UniqueCompletions(BaseModel):
    """Pydantic model for generating unique text completions."""
    completions: list[list[str]] = Field(
        description="A list of completion sets. For single mask texts, each inner list has one completion. For multiple mask texts, each inner list contains completions in order for each mask position. Each completion should be either: 1) A single word, OR 2) A possessive noun phrase like 'goalkeeper's performance', 'student's homework', 'company's profits'. Avoid longer phrases like 'museum that I visited' or 'beautiful sunset today'. Example: [['game', 'it'], ['performance', 'food'], ['movie', 'service']] for two masks."
    )


class ParaphraseResponse(BaseModel):
    """Pydantic model for generating paraphrases of text."""
    paraphrases: list[str] = Field(
        description="A list of paraphrased versions of the input text. Each paraphrase should preserve the original meaning while using different words and sentence structures. Paraphrases should be natural, grammatically correct, and contextually appropriate."
    )


class NegationResponse(BaseModel):
    """Pydantic model for generating negated versions of text."""
    negated_sentences: list[str] = Field(
        description="A list of negation sets for batch processing. Each inner list contains negated versions of one input text. Each negated sentence should express the opposite meaning of the original while being grammatically correct and natural-sounding. Use appropriate negation words (not, never, no, don't, can't, etc.) and maintain the original style and formality level."
    )



__all__ = ['UniqueCompletions', 'ParaphraseResponse', 'NegationResponse']
