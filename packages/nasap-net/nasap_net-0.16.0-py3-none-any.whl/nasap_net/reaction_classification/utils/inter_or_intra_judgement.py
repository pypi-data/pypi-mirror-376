from typing import Literal, TypeAlias

from nasap_net import InterReactionEmbedded, IntraReactionEmbedded

ReactionEmbedded: TypeAlias = (
    IntraReactionEmbedded | InterReactionEmbedded)


def inter_or_intra(
        reaction: ReactionEmbedded) -> Literal["inter", "intra"]:
    if isinstance(reaction, IntraReactionEmbedded):
        return "intra"
    return "inter"
