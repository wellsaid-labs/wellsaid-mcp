from typing import Optional
from pydantic import BaseModel
from wellsaid_mcp.mcp_server import mcp
from wellsaid_mcp.utils import client
from mcp.types import TextContent


class Avatar(BaseModel):
    name:str
    id:int
    style: Optional[str]
    gender: Optional[str]
    accent_type:Optional[str] = None
    characteristics: Optional[list[str]]
    otherTags: Optional[list[str]]
    preview_audio: Optional[str]
    locale: Optional[str]
    language: Optional[str]
    language_variant: Optional[str]
    source: Optional[str]

class AvatarsContent(BaseModel):
    avatars:list[Avatar]

class AvatarCharacteristics(BaseModel):
    characteristics:set[str]

class AvatarCriterion(BaseModel):
    name:str
    options:list[str]
class AvatarCriteria(BaseModel):
    criteria:list[AvatarCriterion]


@mcp.tool(
    description="""Gets a list of available voices and their speaker_ids to use.
    Also has a lot of characteristics and other information about the voices.
    Available options for the different filtering parameters can be found with the get_avatar_criteria function
    
    ⚠️ COST WARNING: This tool makes a paid API call to WellSaid Labs.
    Args:
        gender: Gender of the avatars to fetch. Can be either male or female. Will fetch both if not specified
        characteristics: list of characteristics to filter voices for. An empty list will return all voices.
        You can find a list of available characteristics with the get_avatar_characteristics() function
        language: Language of the voice (e.g. English)
        language_variant: Language variant (e.g. British, United States)
        style: Speaking style (e.g. narration, promotional)
        accent_type: Accent of the voice 
        locale: Locale code (e.g. en_US)
    """
)
def get_avatars(
    gender:str,
    characteristics:list[str],
    language:str,
    language_variant:str,
    style:str,
    accent_type:str,
    locale:str
) -> AvatarsContent:
    # Step 1: Make TTS request
    response = client.get("/avatars")

    if response.status_code != 200:
        return TextContent(type="text", text=f"Error from WellSaid API: {response.text}")

    avatars:list[Avatar] = [Avatar(**item) for item in response.json().get('avatars')]

    if(gender and gender != "") :
        avatars = [obj for obj in avatars if obj.gender == gender]
    
    if characteristics and len(characteristics) > 0:
        filtered_avatars = []
        for avatar in avatars:
            result = any(item.lower() in (s.lower() for s in avatar.characteristics) for item in characteristics)
            if result:
                filtered_avatars.append(avatar)
        avatars = filtered_avatars
    
    if language:
        avatars = [avatar for avatar in avatars if avatar.language == language]
    if language_variant:
        avatars = [avatar for avatar in avatars if avatar.language_variant == language_variant]
    if style:
        avatars = [avatar for avatar in avatars if avatar.style == style]
    if accent_type:
        avatars = [avatar for avatar in avatars if avatar.accent_type == accent_type]
    if locale:
        avatars = [avatar for avatar in avatars if avatar.locale == locale]
    
    return AvatarsContent(
        avatars=avatars
    )

@mcp.tool(
    description="""
    Gets a list of characterstics on wellsaid voice avatars to be used with get_avatars function to filter voices

    """
)
def get_avatar_characteristics(
) -> AvatarCharacteristics:
    # Step 1: Make TTS request
    response = client.get("/avatars")

    if response.status_code != 200:
        return TextContent(type="text", text=f"Error from WellSaid API: {response.text}")

    avatars:list[Avatar] = response.json().get('avatars')



    unique_characteristics = {c for avatar in avatars for c in avatar.get('characteristics')}
    
    return AvatarCharacteristics(
        characteristics=unique_characteristics
    )

@mcp.tool(
    description="""
    Gets options for filtering criteria available for the avatar search, such as gender, characteristics, language, etc
    """
)
def get_avater_criteria()->AvatarCriteria:
    # Step 1: Make TTS request
    response = client.get("/avatars")

    if response.status_code != 200:
        return TextContent(type="text", text=f"Error from WellSaid API: {response.text}")

    avatars:list[Avatar] = response.json().get('avatars')

    criteria = []

    unique_characteristics = {c for avatar in avatars for c in avatar.get('characteristics')}
    criteria.append(AvatarCriterion(name="characteristic",options=list(unique_characteristics)))

    genders = {avatar.get('gender') for avatar in avatars if avatar.get('gender') is not None}
    criteria.append(AvatarCriterion(name="gender",options=list(genders)))
    styles = {avatar.get('style') for avatar in avatars if avatar.get('style') is not None}
    criteria.append(AvatarCriterion(name="style",options=list(styles)))
    accent_types = {avatar.get('accent_type') for avatar in avatars if avatar.get('accent_type') is not None}
    criteria.append(AvatarCriterion(name="accent_type",options=list(accent_types)))
    languages = {avatar.get('language') for avatar in avatars if avatar.get('language') is not None}
    criteria.append(AvatarCriterion(name="language",options=list(languages)))
    language_variants = {avatar.get('language_variant') for avatar in avatars if avatar.get('language_variant') is not None}
    criteria.append(AvatarCriterion(name="language_variant",options=list(language_variants)))
    locales = {avatar.get('locale') for avatar in avatars if avatar.get('locale') is not None}
    criteria.append(AvatarCriterion(name="locale",options=list(locales)))
    return AvatarCriteria(criteria=criteria)
    
   