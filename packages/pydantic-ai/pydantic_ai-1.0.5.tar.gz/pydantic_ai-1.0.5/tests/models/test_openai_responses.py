import json
from dataclasses import replace
from typing import Any, cast

import pytest
from inline_snapshot import snapshot
from pydantic import BaseModel
from typing_extensions import TypedDict

from pydantic_ai.agent import Agent
from pydantic_ai.builtin_tools import CodeExecutionTool, WebSearchTool
from pydantic_ai.exceptions import ModelHTTPError, ModelRetry
from pydantic_ai.messages import (
    BinaryContent,
    DocumentUrl,
    FinalResultEvent,
    ImageUrl,
    ModelRequest,
    ModelResponse,
    PartDeltaEvent,
    PartStartEvent,
    RetryPromptPart,
    TextPart,
    TextPartDelta,
    ThinkingPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)
from pydantic_ai.output import NativeOutput, PromptedOutput, TextOutput, ToolOutput
from pydantic_ai.profiles.openai import openai_model_profile
from pydantic_ai.tools import ToolDefinition
from pydantic_ai.usage import RequestUsage, RunUsage

from ..conftest import IsDatetime, IsStr, TestEnv, try_import
from ..parts_from_messages import part_types_from_messages
from .mock_openai import MockOpenAIResponses, response_message

with try_import() as imports_successful:
    from openai.types.responses.response_output_message import Content, ResponseOutputMessage, ResponseOutputText
    from openai.types.responses.response_reasoning_item import ResponseReasoningItem
    from openai.types.responses.response_usage import ResponseUsage

    from pydantic_ai.models.anthropic import AnthropicModel, AnthropicModelSettings
    from pydantic_ai.models.openai import OpenAIResponsesModel, OpenAIResponsesModelSettings
    from pydantic_ai.providers.anthropic import AnthropicProvider
    from pydantic_ai.providers.openai import OpenAIProvider

pytestmark = [
    pytest.mark.skipif(not imports_successful(), reason='openai not installed'),
    pytest.mark.anyio,
    pytest.mark.vcr,
]


def test_openai_responses_model(env: TestEnv):
    env.set('OPENAI_API_KEY', 'test')
    model = OpenAIResponsesModel('gpt-4o')
    assert model.model_name == 'gpt-4o'
    assert model.system == 'openai'


async def test_openai_responses_model_simple_response(allow_model_requests: None, openai_api_key: str):
    model = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key=openai_api_key))
    agent = Agent(model=model)
    result = await agent.run('What is the capital of France?')
    assert result.output == snapshot('The capital of France is Paris.')


async def test_openai_responses_model_simple_response_with_tool_call(allow_model_requests: None, openai_api_key: str):
    model = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key=openai_api_key))

    agent = Agent(model=model)

    @agent.tool_plain
    async def get_capital(country: str) -> str:
        return 'Potato City'

    result = await agent.run('What is the capital of PotatoLand?')
    assert result.output == snapshot('The capital of PotatoLand is Potato City.')


async def test_openai_responses_output_type(allow_model_requests: None, openai_api_key: str):
    model = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key=openai_api_key))

    class MyOutput(TypedDict):
        name: str
        age: int

    agent = Agent(model=model, output_type=MyOutput)
    result = await agent.run('Give me the name and age of Brazil, Argentina, and Chile.')
    assert result.output == snapshot({'name': 'Brazil', 'age': 2023})


async def test_openai_responses_reasoning_effort(allow_model_requests: None, openai_api_key: str):
    model = OpenAIResponsesModel('o3-mini', provider=OpenAIProvider(api_key=openai_api_key))
    agent = Agent(model=model, model_settings=OpenAIResponsesModelSettings(openai_reasoning_effort='low'))
    result = await agent.run(
        'Explain me how to cook uruguayan alfajor. Do not send whitespaces at the end of the lines.'
    )
    assert [line.strip() for line in result.output.splitlines()] == snapshot(
        [
            'Ingredients for the dough:',
            '• 300 g cornstarch',
            '• 200 g flour',
            '• 150 g powdered sugar',
            '• 200 g unsalted butter',
            '• 3 egg yolks',
            '• Zest of 1 lemon',
            '• 1 teaspoon vanilla extract',
            '• A pinch of salt',
            '',
            'Ingredients for the filling (dulce de leche):',
            '• 400 g dulce de leche',
            '',
            'Optional coating:',
            '• Powdered sugar for dusting',
            '• Grated coconut',
            '• Crushed peanuts or walnuts',
            '• Melted chocolate',
            '',
            'Steps:',
            '1. In a bowl, mix together the cornstarch, flour, powdered sugar, and salt.',
            '2. Add the unsalted butter cut into small pieces. Work it into the dry ingredients until the mixture resembles coarse breadcrumbs.',
            '3. Incorporate the egg yolks, lemon zest, and vanilla extract. Mix until you obtain a smooth and homogeneous dough.',
            '4. Wrap the dough in plastic wrap and let it rest in the refrigerator for at least one hour.',
            '5. Meanwhile, prepare a clean workspace by lightly dusting it with flour.',
            '6. Roll out the dough on the working surface until it is about 0.5 cm thick.',
            '7. Use a round cutter (approximately 3-4 cm in diameter) to cut out circles. Re-roll any scraps to maximize the number of cookies.',
            '8. Arrange the circles on a baking sheet lined with parchment paper.',
            '9. Preheat the oven to 180°C (350°F) and bake the cookies for about 10-12 minutes until they are lightly golden at the edges. They should remain soft.',
            '10. Remove the cookies from the oven and allow them to cool completely on a rack.',
            '11. Once the cookies are cool, spread dulce de leche on the flat side of one cookie and sandwich it with another.',
            '12. If desired, roll the edges of the alfajores in powdered sugar, grated coconut, crushed nuts, or dip them in melted chocolate.',
            '13. Allow any coatings to set before serving.',
            '',
            'Enjoy your homemade Uruguayan alfajores!',
        ]
    )


async def test_openai_responses_reasoning_generate_summary(allow_model_requests: None, openai_api_key: str):
    model = OpenAIResponsesModel('computer-use-preview', provider=OpenAIProvider(api_key=openai_api_key))
    agent = Agent(
        model=model,
        model_settings=OpenAIResponsesModelSettings(
            openai_reasoning_summary='concise',
            openai_truncation='auto',
        ),
    )
    result = await agent.run('What should I do to cross the street?')
    assert result.output == snapshot("""\
To cross the street safely, follow these steps:

1. **Use a Crosswalk**: Always use a designated crosswalk or pedestrian crossing whenever available.
2. **Press the Button**: If there is a pedestrian signal button, press it and wait for the signal.
3. **Look Both Ways**: Look left, right, and left again before stepping off the curb.
4. **Wait for the Signal**: Cross only when the pedestrian signal indicates it is safe to do so or when there is a clear gap in traffic.
5. **Stay Alert**: Be mindful of turning vehicles and stay attentive while crossing.
6. **Walk, Don't Run**: Walk across the street; running can increase the risk of falling or not noticing an oncoming vehicle.

Always follow local traffic rules and be cautious, even when crossing at a crosswalk. Safety is the priority.\
""")


async def test_openai_responses_system_prompt(allow_model_requests: None, openai_api_key: str):
    model = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key=openai_api_key))
    agent = Agent(model=model, system_prompt='You are a helpful assistant.')
    result = await agent.run('What is the capital of France?')
    assert result.output == snapshot('The capital of France is Paris.')


async def test_openai_responses_model_retry(allow_model_requests: None, openai_api_key: str):
    model = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key=openai_api_key))
    agent = Agent(model=model)

    @agent.tool_plain
    async def get_location(loc_name: str) -> str:
        if loc_name == 'London':
            return json.dumps({'lat': 51, 'lng': 0})
        else:
            raise ModelRetry('Wrong location, I only know about "London".')

    result = await agent.run('What is the location of Londos and London?')
    assert result.all_messages() == snapshot(
        [
            ModelRequest(
                parts=[
                    UserPromptPart(
                        content='What is the location of Londos and London?',
                        timestamp=IsDatetime(),
                    )
                ]
            ),
            ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name='get_location',
                        args='{"loc_name":"Londos"}',
                        tool_call_id=IsStr(),
                    ),
                    ToolCallPart(
                        tool_name='get_location',
                        args='{"loc_name":"London"}',
                        tool_call_id=IsStr(),
                    ),
                ],
                usage=RequestUsage(details={'reasoning_tokens': 0}),
                model_name='gpt-4o-2024-08-06',
                timestamp=IsDatetime(),
                provider_name='openai',
                provider_details={'finish_reason': 'completed'},
                provider_response_id='resp_67e547c48c9481918c5c4394464ce0c60ae6111e84dd5c08',
                finish_reason='stop',
            ),
            ModelRequest(
                parts=[
                    RetryPromptPart(
                        content='Wrong location, I only know about "London".',
                        tool_name='get_location',
                        tool_call_id=IsStr(),
                        timestamp=IsDatetime(),
                    ),
                    ToolReturnPart(
                        tool_name='get_location',
                        content='{"lat": 51, "lng": 0}',
                        tool_call_id=IsStr(),
                        timestamp=IsDatetime(),
                    ),
                ]
            ),
            ModelResponse(
                parts=[
                    TextPart(
                        content="""\
It seems "Londos" might be incorrect or unknown. If you meant something else, please clarify.

For **London**, it's located at approximately latitude 51° N and longitude 0° W.\
""",
                        id='msg_67e547c615ec81918d6671a184f82a1803a2086afed73b47',
                    )
                ],
                usage=RequestUsage(input_tokens=335, output_tokens=44, details={'reasoning_tokens': 0}),
                model_name='gpt-4o-2024-08-06',
                timestamp=IsDatetime(),
                provider_name='openai',
                provider_details={'finish_reason': 'completed'},
                provider_response_id='resp_67e547c5a2f08191802a1f43620f348503a2086afed73b47',
                finish_reason='stop',
            ),
        ]
    )


@pytest.mark.vcr()
async def test_image_as_binary_content_tool_response(
    allow_model_requests: None, image_content: BinaryContent, openai_api_key: str
):
    m = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key=openai_api_key))
    agent = Agent(m)

    @agent.tool_plain
    async def get_image() -> BinaryContent:
        return image_content

    result = await agent.run(['What fruit is in the image you can get from the get_image tool?'])
    assert result.all_messages() == snapshot(
        [
            ModelRequest(
                parts=[
                    UserPromptPart(
                        content=['What fruit is in the image you can get from the get_image tool?'],
                        timestamp=IsDatetime(),
                    )
                ]
            ),
            ModelResponse(
                parts=[ToolCallPart(tool_name='get_image', args='{}', tool_call_id=IsStr())],
                usage=RequestUsage(input_tokens=40, output_tokens=11, details={'reasoning_tokens': 0}),
                model_name='gpt-4o-2024-08-06',
                timestamp=IsDatetime(),
                provider_name='openai',
                provider_details={'finish_reason': 'completed'},
                provider_response_id='resp_681134d3aa3481919ca581a267db1e510fe7a5a4e2123dc3',
                finish_reason='stop',
            ),
            ModelRequest(
                parts=[
                    ToolReturnPart(
                        tool_name='get_image',
                        content='See file 1c8566',
                        tool_call_id='call_FLm3B1f8QAan0KpbUXhNY8bA|fc_681134d47cf48191b3f62e4d28b6c3820fe7a5a4e2123dc3',
                        timestamp=IsDatetime(),
                    ),
                    UserPromptPart(
                        content=[
                            'This is file 1c8566:',
                            image_content,
                        ],
                        timestamp=IsDatetime(),
                    ),
                ]
            ),
            ModelResponse(
                parts=[
                    TextPart(
                        content='The fruit in the image is a kiwi.',
                        id='msg_681134d770d881919f3a3148badde27802cbfeaababb040c',
                    )
                ],
                usage=RequestUsage(input_tokens=1185, output_tokens=11, details={'reasoning_tokens': 0}),
                model_name='gpt-4o-2024-08-06',
                timestamp=IsDatetime(),
                provider_name='openai',
                provider_details={'finish_reason': 'completed'},
                provider_response_id='resp_681134d53c48819198ce7b89db78dffd02cbfeaababb040c',
                finish_reason='stop',
            ),
        ]
    )


async def test_image_as_binary_content_input(
    allow_model_requests: None, image_content: BinaryContent, openai_api_key: str
):
    m = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key=openai_api_key))
    agent = Agent(m)

    result = await agent.run(['What fruit is in the image?', image_content])
    assert result.output == snapshot('The fruit in the image is a kiwi.')


async def test_openai_responses_audio_as_binary_content_input(
    allow_model_requests: None, audio_content: BinaryContent, openai_api_key: str
):
    m = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key=openai_api_key))
    agent = Agent(m)

    with pytest.raises(NotImplementedError):
        await agent.run(['Whose name is mentioned in the audio?', audio_content])


async def test_openai_responses_document_as_binary_content_input(
    allow_model_requests: None, document_content: BinaryContent, openai_api_key: str
):
    m = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key=openai_api_key))
    agent = Agent(m)

    result = await agent.run(['What is in the document?', document_content])
    assert result.output == snapshot('The document contains the text "Dummy PDF file."')


async def test_openai_responses_document_url_input(allow_model_requests: None, openai_api_key: str):
    m = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key=openai_api_key))
    agent = Agent(m)

    document_url = DocumentUrl(url='https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf')

    result = await agent.run(['What is the main content on this document?', document_url])
    assert result.output == snapshot(
        'The main content of this document is a simple text placeholder: "Dummy PDF file."'
    )


async def test_openai_responses_text_document_url_input(allow_model_requests: None, openai_api_key: str):
    m = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key=openai_api_key))
    agent = Agent(m)

    text_document_url = DocumentUrl(url='https://example-files.online-convert.com/document/txt/example.txt')

    result = await agent.run(['What is the main content on this document?', text_document_url])
    assert result.output == snapshot(
        'The main content of this document is an example of a TXT file type, with an explanation of the use of placeholder names like "John Doe" and "Jane Doe" in legal, medical, and other contexts. It discusses the practice in the U.S. and Canada, mentions equivalent practices in other English-speaking countries, and touches on cultural references. The document also notes that it\'s an example file created by an online conversion tool, with content sourced from Wikipedia under a Creative Commons license.'
    )


async def test_openai_responses_image_url_input(allow_model_requests: None, openai_api_key: str):
    m = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key=openai_api_key))
    agent = Agent(m)

    result = await agent.run(
        [
            'hello',
            ImageUrl(url='https://t3.ftcdn.net/jpg/00/85/79/92/360_F_85799278_0BBGV9OAdQDTLnKwAPBCcg1J7QtiieJY.jpg'),
        ]
    )
    assert result.output == snapshot("Hello! I see you've shared an image of a potato. How can I assist you today?")


async def test_openai_responses_stream(allow_model_requests: None, openai_api_key: str):
    model = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key=openai_api_key))
    agent = Agent(model=model)

    @agent.tool_plain
    async def get_capital(country: str) -> str:
        return 'Paris'

    output_text: list[str] = []
    async with agent.run_stream('What is the capital of France?') as result:
        async for output in result.stream_text():
            output_text.append(output)
        async for response, is_last in result.stream_responses(debounce_by=None):
            if is_last:
                assert response == snapshot(
                    ModelResponse(
                        parts=[
                            TextPart(
                                content='The capital of France is Paris.',
                                id='msg_67e554a28bec8191b56d3e2331eff88006c52f0e511c76ed',
                            )
                        ],
                        usage=RequestUsage(input_tokens=278, output_tokens=9, details={'reasoning_tokens': 0}),
                        model_name='gpt-4o-2024-08-06',
                        timestamp=IsDatetime(),
                        provider_name='openai',
                        provider_details={'finish_reason': 'completed'},
                        provider_response_id='resp_67e554a21aa88191b65876ac5e5bbe0406c52f0e511c76ed',
                        finish_reason='stop',
                    )
                )

    assert output_text == snapshot(['The capital of France is Paris.'])


async def test_openai_responses_model_http_error(allow_model_requests: None, openai_api_key: str):
    """Set temperature to -1 to trigger an error, given only values between 0 and 1 are allowed."""
    model = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key=openai_api_key))
    agent = Agent(model=model, model_settings=OpenAIResponsesModelSettings(temperature=-1))

    with pytest.raises(ModelHTTPError):
        async with agent.run_stream('What is the capital of France?'):
            ...  # pragma: lax no cover


async def test_openai_responses_model_builtin_tools(allow_model_requests: None, openai_api_key: str):
    model = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key=openai_api_key))
    settings = OpenAIResponsesModelSettings(openai_builtin_tools=[{'type': 'web_search_preview'}])
    agent = Agent(model=model, model_settings=settings)
    result = await agent.run('Give me the best news about LLMs from the last 24 hours. Be short.')

    # NOTE: We don't have the tool call because OpenAI calls the tool internally.
    assert result.all_messages() == snapshot(
        [
            ModelRequest(
                parts=[
                    UserPromptPart(
                        content='Give me the best news about LLMs from the last 24 hours. Be short.',
                        timestamp=IsDatetime(),
                    )
                ]
            ),
            ModelResponse(
                parts=[
                    TextPart(
                        content="""\
OpenAI's recent launch of GPT-5 has faced mixed reactions. Despite strong benchmark performance and early praise, users have reported issues like errors in basic math and geography. CEO Sam Altman has acknowledged these concerns and assured that improvements are underway. ([axios.com](https://www.axios.com/2025/08/12/gpt-5-bumpy-launch-openai?utm_source=openai))


## OpenAI's GPT-5 Launch Faces Mixed Reactions:
- [OpenAI's big GPT-5 launch gets bumpy](https://www.axios.com/2025/08/12/gpt-5-bumpy-launch-openai?utm_source=openai) \
""",
                        id='msg_689b7c951b7481968513d007e75151fd07450cfc2d48b975',
                    )
                ],
                usage=RequestUsage(input_tokens=320, output_tokens=159, details={'reasoning_tokens': 0}),
                model_name='gpt-4o-2024-08-06',
                timestamp=IsDatetime(),
                provider_name='openai',
                provider_details={'finish_reason': 'completed'},
                provider_response_id='resp_689b7c90010c8196ac0efd68b021490f07450cfc2d48b975',
                finish_reason='stop',
            ),
        ]
    )


@pytest.mark.vcr()
async def test_openai_responses_model_instructions(allow_model_requests: None, openai_api_key: str):
    m = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key=openai_api_key))
    agent = Agent(m, instructions='You are a helpful assistant.')

    result = await agent.run('What is the capital of France?')
    assert result.all_messages() == snapshot(
        [
            ModelRequest(
                parts=[UserPromptPart(content='What is the capital of France?', timestamp=IsDatetime())],
                instructions='You are a helpful assistant.',
            ),
            ModelResponse(
                parts=[
                    TextPart(
                        content='The capital of France is Paris.',
                        id='msg_67f3fdfe15b881918d7b865e6a5f4fb1003bc73febb56d77',
                    )
                ],
                usage=RequestUsage(input_tokens=24, output_tokens=8, details={'reasoning_tokens': 0}),
                model_name='gpt-4o-2024-08-06',
                timestamp=IsDatetime(),
                provider_name='openai',
                provider_details={'finish_reason': 'completed'},
                provider_response_id='resp_67f3fdfd9fa08191a3d5825db81b8df6003bc73febb56d77',
                finish_reason='stop',
            ),
        ]
    )


async def test_openai_responses_model_web_search_tool(allow_model_requests: None, openai_api_key: str):
    m = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key=openai_api_key))
    agent = Agent(m, instructions='You are a helpful assistant.', builtin_tools=[WebSearchTool()])

    result = await agent.run('What day is it today?')
    assert result.output == snapshot("""\
Today is Wednesday, May 14, 2025.

## Weather for San Francisco, CA:
Current Conditions: Mostly clear, 50°F (10°C)

Daily Forecast:
* Wednesday, May 14: Low: 51°F (10°C), High: 65°F (18°C), Description: Areas of low clouds early; otherwise, mostly sunny
* Thursday, May 15: Low: 53°F (12°C), High: 66°F (19°C), Description: Areas of low clouds, then sun
* Friday, May 16: Low: 53°F (12°C), High: 64°F (18°C), Description: Partly sunny
* Saturday, May 17: Low: 52°F (11°C), High: 63°F (17°C), Description: Low clouds breaking for some sun; breezy in the afternoon
* Sunday, May 18: Low: 51°F (10°C), High: 68°F (20°C), Description: Clouds yielding to sun
* Monday, May 19: Low: 53°F (12°C), High: 68°F (20°C), Description: Sunny
* Tuesday, May 20: Low: 52°F (11°C), High: 70°F (21°C), Description: Mostly sunny
 \
""")


async def test_openai_responses_model_web_search_tool_with_user_location(
    allow_model_requests: None, openai_api_key: str
):
    m = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key=openai_api_key))
    agent = Agent(
        m,
        instructions='You are a helpful assistant.',
        builtin_tools=[WebSearchTool(user_location={'city': 'Utrecht', 'region': 'NL'})],
    )

    result = await agent.run('What is the current temperature?')
    assert result.output == snapshot("""\
As of 12:58 PM on Wednesday, May 14, 2025, in Utrecht, Netherlands, the weather is sunny with a temperature of 22°C (71°F).

## Weather for Utrecht, Netherlands:
Current Conditions: Sunny, 71°F (22°C)

Daily Forecast:
* Wednesday, May 14: Low: 48°F (9°C), High: 71°F (22°C), Description: Clouds yielding to sun
* Thursday, May 15: Low: 43°F (6°C), High: 67°F (20°C), Description: After a cloudy start, sun returns
* Friday, May 16: Low: 45°F (7°C), High: 64°F (18°C), Description: Mostly sunny
* Saturday, May 17: Low: 47°F (9°C), High: 68°F (20°C), Description: Mostly sunny
* Sunday, May 18: Low: 47°F (8°C), High: 68°F (20°C), Description: Some sun
* Monday, May 19: Low: 49°F (9°C), High: 70°F (21°C), Description: Delightful with partial sunshine
* Tuesday, May 20: Low: 49°F (10°C), High: 72°F (22°C), Description: Warm with sunshine and a few clouds
 \
""")


async def test_openai_responses_model_web_search_tool_with_invalid_region(
    allow_model_requests: None, openai_api_key: str
):
    m = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key=openai_api_key))
    agent = Agent(
        m,
        instructions='You are a helpful assistant.',
        builtin_tools=[WebSearchTool(user_location={'city': 'Salvador', 'region': 'BRLO'})],
    )

    result = await agent.run('What is the current temperature?')
    assert result.output == snapshot("""\
As of 12:15 PM on Thursday, August 7, 2025, in Salvador, Brazil, the current weather conditions are:

- **Temperature:** 84°F (29°C)
- **Feels Like:** 88°F (31°C)
- **Condition:** Sunny
- **Wind:** East at 16 mph (25 km/h)
- **Humidity:** 65%
- **Dew Point:** 71°F (22°C)
- **Pressure:** 29.88 in (1012 mb)
- **Visibility:** 8 miles (13 km)

([aerisweather.com](https://www.aerisweather.com/weather/local/br/salvador?utm_source=openai))

The forecast for today indicates partly cloudy skies with temperatures remaining around 84°F (29°C) this afternoon. \
""")


async def test_openai_responses_model_web_search_tool_stream(allow_model_requests: None, openai_api_key: str):
    m = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key=openai_api_key))
    agent = Agent(m, instructions='You are a helpful assistant.', builtin_tools=[WebSearchTool()])

    event_parts: list[Any] = []
    async with agent.iter(user_prompt='Give me the top 3 news in the world today.') as agent_run:
        async for node in agent_run:
            if Agent.is_model_request_node(node) or Agent.is_call_tools_node(node):
                async with node.stream(agent_run.ctx) as request_stream:
                    async for event in request_stream:
                        event_parts.append(event)

    assert event_parts.pop(0) == snapshot(
        PartStartEvent(
            index=0, part=TextPart(content='Here', id='msg_68949c6f2ec4819180d56b4ad8ce5469004c84cbcf4b67dc')
        )
    )
    assert event_parts.pop(0) == snapshot(FinalResultEvent(tool_name=None, tool_call_id=None))
    assert ''.join(event.delta.content_delta for event in event_parts) == snapshot("""\
 are the top three news stories from around the world as of August 7, 2025:

1. **U.S. Imposes New Tariffs Amid Market Optimism**

   The United States has implemented new tariffs ranging from 10% to 50% on imports from multiple countries. Despite this, global markets have shown resilience, buoyed by expectations of interest rate cuts and positive earnings reports. Notably, exemptions were granted to Taiwan and South Korea, shielding major chipmakers like TSMC, Samsung, and SK Hynix from the highest levies. ([reuters.com](https://www.reuters.com/business/finance/global-markets-view-usa-2025-08-07/?utm_source=openai))

2. **Ghanaian Ministers Killed in Helicopter Crash**

   Ghana's Defence Minister Edward Omane Boamah and Environment Minister Ibrahim Murtala Muhammed, along with six others, have died in a military helicopter crash in the Ashanti region. The incident has been described as a "national tragedy" by Chief of Staff Julius Debrah. ([anewz.tv](https://anewz.tv/world/world-news/11722/anewz-morning-brief-7th-august-2025/news?utm_source=openai))

3. **Massive Wildfire in France Claims Lives**

   A significant wildfire in southern France's Aude region has resulted in at least one death and nine injuries. The fire, which began on August 6, has destroyed or damaged 25 homes, with over 1,800 firefighters working to control the blaze. ([anewz.tv](https://anewz.tv/world/world-news/11722/anewz-morning-brief-7th-august-2025/news?utm_source=openai))

Please note that news developments are continually evolving. For the most current information, refer to reputable news sources. \
""")


async def test_openai_responses_code_execution_tool(allow_model_requests: None, openai_api_key: str):
    m = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key=openai_api_key))
    agent = Agent(m, instructions='You are a helpful assistant.', builtin_tools=[CodeExecutionTool()])

    result = await agent.run('What is 3 * 12390?')
    # NOTE: OpenAI doesn't return neither the `BuiltinToolCallPart` nor the `BuiltinToolReturnPart`.
    assert part_types_from_messages(result.all_messages()) == snapshot([[UserPromptPart], [TextPart]])


async def test_openai_responses_code_execution_tool_stream(allow_model_requests: None, openai_api_key: str):
    m = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key=openai_api_key))
    agent = Agent(m, instructions='You are a helpful assistant.', builtin_tools=[CodeExecutionTool()])

    event_parts: list[Any] = []
    async with agent.iter(user_prompt='What is 3 * 12390?') as agent_run:
        async for node in agent_run:
            if Agent.is_model_request_node(node) or Agent.is_call_tools_node(node):
                async with node.stream(agent_run.ctx) as request_stream:
                    async for event in request_stream:
                        event_parts.append(event)

    assert event_parts == snapshot(
        [
            PartStartEvent(
                index=0, part=TextPart(content='\\(', id='msg_6894960732d4819284cbfad4b9a1301d0f6766ea87e53a34')
            ),
            FinalResultEvent(tool_name=None, tool_call_id=None),
            PartDeltaEvent(index=0, delta=TextPartDelta(content_delta='3')),
            PartDeltaEvent(index=0, delta=TextPartDelta(content_delta=' \\')),
            PartDeltaEvent(index=0, delta=TextPartDelta(content_delta='times')),
            PartDeltaEvent(index=0, delta=TextPartDelta(content_delta=' ')),
            PartDeltaEvent(index=0, delta=TextPartDelta(content_delta='123')),
            PartDeltaEvent(index=0, delta=TextPartDelta(content_delta='90')),
            PartDeltaEvent(index=0, delta=TextPartDelta(content_delta=' =')),
            PartDeltaEvent(index=0, delta=TextPartDelta(content_delta=' ')),
            PartDeltaEvent(index=0, delta=TextPartDelta(content_delta='371')),
            PartDeltaEvent(index=0, delta=TextPartDelta(content_delta='70')),
            PartDeltaEvent(index=0, delta=TextPartDelta(content_delta='\\')),
            PartDeltaEvent(index=0, delta=TextPartDelta(content_delta=').')),
        ]
    )


def test_model_profile_strict_not_supported():
    my_tool = ToolDefinition(
        name='my_tool',
        description='This is my tool',
        parameters_json_schema={'type': 'object', 'title': 'Result', 'properties': {'spam': {'type': 'number'}}},
        strict=True,
    )

    m = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key='foobar'))
    tool_param = m._map_tool_definition(my_tool)  # type: ignore[reportPrivateUsage]

    assert tool_param == snapshot(
        {
            'name': 'my_tool',
            'parameters': {'type': 'object', 'title': 'Result', 'properties': {'spam': {'type': 'number'}}},
            'type': 'function',
            'description': 'This is my tool',
            'strict': True,
        }
    )

    # Some models don't support strict tool definitions
    m = OpenAIResponsesModel(
        'gpt-4o',
        provider=OpenAIProvider(api_key='foobar'),
        profile=replace(openai_model_profile('gpt-4o'), openai_supports_strict_tool_definition=False),
    )
    tool_param = m._map_tool_definition(my_tool)  # type: ignore[reportPrivateUsage]

    assert tool_param == snapshot(
        {
            'name': 'my_tool',
            'parameters': {'type': 'object', 'title': 'Result', 'properties': {'spam': {'type': 'number'}}},
            'type': 'function',
            'description': 'This is my tool',
            'strict': False,
        }
    )


@pytest.mark.vcr()
async def test_reasoning_model_with_temperature(allow_model_requests: None, openai_api_key: str):
    m = OpenAIResponsesModel('o3-mini', provider=OpenAIProvider(api_key=openai_api_key))
    agent = Agent(m, model_settings=OpenAIResponsesModelSettings(temperature=0.5))
    result = await agent.run('What is the capital of Mexico?')
    assert result.output == snapshot(
        'The capital of Mexico is Mexico City. It serves as the political, cultural, and economic heart of the country and is one of the largest metropolitan areas in the world.'
    )


@pytest.mark.vcr()
async def test_tool_output(allow_model_requests: None, openai_api_key: str):
    m = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key=openai_api_key))

    class CityLocation(BaseModel):
        city: str
        country: str

    agent = Agent(m, output_type=ToolOutput(CityLocation))

    @agent.tool_plain
    async def get_user_country() -> str:
        return 'Mexico'

    result = await agent.run('What is the largest city in the user country?')
    assert result.output == snapshot(CityLocation(city='Mexico City', country='Mexico'))

    assert result.all_messages() == snapshot(
        [
            ModelRequest(
                parts=[
                    UserPromptPart(
                        content='What is the largest city in the user country?',
                        timestamp=IsDatetime(),
                    )
                ]
            ),
            ModelResponse(
                parts=[ToolCallPart(tool_name='get_user_country', args='{}', tool_call_id=IsStr())],
                usage=RequestUsage(input_tokens=62, output_tokens=12, details={'reasoning_tokens': 0}),
                model_name='gpt-4o-2024-08-06',
                timestamp=IsDatetime(),
                provider_name='openai',
                provider_details={'finish_reason': 'completed'},
                provider_response_id='resp_68477f0b40a8819cb8d55594bc2c232a001fd29e2d5573f7',
                finish_reason='stop',
            ),
            ModelRequest(
                parts=[
                    ToolReturnPart(
                        tool_name='get_user_country',
                        content='Mexico',
                        tool_call_id='call_ZWkVhdUjupo528U9dqgFeRkH|fc_68477f0bb8e4819cba6d781e174d77f8001fd29e2d5573f7',
                        timestamp=IsDatetime(),
                    )
                ]
            ),
            ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name='final_result',
                        args='{"city":"Mexico City","country":"Mexico"}',
                        tool_call_id='call_iFBd0zULhSZRR908DfH73VwN|fc_68477f0c91cc819e8024e7e633f0f09401dc81d4bc91f560',
                    )
                ],
                usage=RequestUsage(input_tokens=85, output_tokens=20, details={'reasoning_tokens': 0}),
                model_name='gpt-4o-2024-08-06',
                timestamp=IsDatetime(),
                provider_name='openai',
                provider_details={'finish_reason': 'completed'},
                provider_response_id='resp_68477f0bfda8819ea65458cd7cc389b801dc81d4bc91f560',
                finish_reason='stop',
            ),
            ModelRequest(
                parts=[
                    ToolReturnPart(
                        tool_name='final_result',
                        content='Final result processed.',
                        tool_call_id='call_iFBd0zULhSZRR908DfH73VwN|fc_68477f0c91cc819e8024e7e633f0f09401dc81d4bc91f560',
                        timestamp=IsDatetime(),
                    )
                ]
            ),
        ]
    )


@pytest.mark.vcr()
async def test_text_output_function(allow_model_requests: None, openai_api_key: str):
    m = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key=openai_api_key))

    def upcase(text: str) -> str:
        return text.upper()

    agent = Agent(m, output_type=TextOutput(upcase))

    @agent.tool_plain
    async def get_user_country() -> str:
        return 'Mexico'

    result = await agent.run('What is the largest city in the user country?')
    assert result.output == snapshot('THE LARGEST CITY IN MEXICO IS MEXICO CITY.')

    assert result.all_messages() == snapshot(
        [
            ModelRequest(
                parts=[
                    UserPromptPart(
                        content='What is the largest city in the user country?',
                        timestamp=IsDatetime(),
                    )
                ]
            ),
            ModelResponse(
                parts=[
                    ToolCallPart(
                        tool_name='get_user_country',
                        args='{}',
                        tool_call_id='call_aTJhYjzmixZaVGqwl5gn2Ncr|fc_68477f0dff5c819ea17a1ffbaea621e00356a60c98816d6a',
                    )
                ],
                usage=RequestUsage(input_tokens=36, output_tokens=12, details={'reasoning_tokens': 0}),
                model_name='gpt-4o-2024-08-06',
                timestamp=IsDatetime(),
                provider_name='openai',
                provider_details={'finish_reason': 'completed'},
                provider_response_id='resp_68477f0d9494819ea4f123bba707c9ee0356a60c98816d6a',
                finish_reason='stop',
            ),
            ModelRequest(
                parts=[
                    ToolReturnPart(
                        tool_name='get_user_country',
                        content='Mexico',
                        tool_call_id='call_aTJhYjzmixZaVGqwl5gn2Ncr|fc_68477f0dff5c819ea17a1ffbaea621e00356a60c98816d6a',
                        timestamp=IsDatetime(),
                    )
                ]
            ),
            ModelResponse(
                parts=[
                    TextPart(
                        content='The largest city in Mexico is Mexico City.',
                        id='msg_68477f0ebf54819d88a44fa87aadaff503434b607c02582d',
                    )
                ],
                usage=RequestUsage(input_tokens=59, output_tokens=11, details={'reasoning_tokens': 0}),
                model_name='gpt-4o-2024-08-06',
                timestamp=IsDatetime(),
                provider_name='openai',
                provider_details={'finish_reason': 'completed'},
                provider_response_id='resp_68477f0e2b28819d9c828ef4ee526d6a03434b607c02582d',
                finish_reason='stop',
            ),
        ]
    )


@pytest.mark.vcr()
async def test_native_output(allow_model_requests: None, openai_api_key: str):
    m = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key=openai_api_key))

    class CityLocation(BaseModel):
        """A city and its country."""

        city: str
        country: str

    agent = Agent(m, output_type=NativeOutput(CityLocation))

    @agent.tool_plain
    async def get_user_country() -> str:
        return 'Mexico'

    result = await agent.run('What is the largest city in the user country?')
    assert result.output == snapshot(CityLocation(city='Mexico City', country='Mexico'))

    assert result.all_messages() == snapshot(
        [
            ModelRequest(
                parts=[
                    UserPromptPart(
                        content='What is the largest city in the user country?',
                        timestamp=IsDatetime(),
                    )
                ]
            ),
            ModelResponse(
                parts=[ToolCallPart(tool_name='get_user_country', args='{}', tool_call_id=IsStr())],
                usage=RequestUsage(input_tokens=66, output_tokens=12, details={'reasoning_tokens': 0}),
                model_name='gpt-4o-2024-08-06',
                timestamp=IsDatetime(),
                provider_name='openai',
                provider_details={'finish_reason': 'completed'},
                provider_response_id='resp_68477f0f220081a1a621d6bcdc7f31a50b8591d9001d2329',
                finish_reason='stop',
            ),
            ModelRequest(
                parts=[
                    ToolReturnPart(
                        tool_name='get_user_country',
                        content='Mexico',
                        tool_call_id='call_tTAThu8l2S9hNky2krdwijGP|fc_68477f0fa7c081a19a525f7c6f180f310b8591d9001d2329',
                        timestamp=IsDatetime(),
                    )
                ]
            ),
            ModelResponse(
                parts=[
                    TextPart(
                        content='{"city":"Mexico City","country":"Mexico"}',
                        id='msg_68477f10846c81929f1e833b0785e6f3020197534e39cc1f',
                    )
                ],
                usage=RequestUsage(input_tokens=89, output_tokens=16, details={'reasoning_tokens': 0}),
                model_name='gpt-4o-2024-08-06',
                timestamp=IsDatetime(),
                provider_name='openai',
                provider_details={'finish_reason': 'completed'},
                provider_response_id='resp_68477f0fde708192989000a62809c6e5020197534e39cc1f',
                finish_reason='stop',
            ),
        ]
    )


@pytest.mark.vcr()
async def test_native_output_multiple(allow_model_requests: None, openai_api_key: str):
    m = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key=openai_api_key))

    class CityLocation(BaseModel):
        city: str
        country: str

    class CountryLanguage(BaseModel):
        country: str
        language: str

    agent = Agent(m, output_type=NativeOutput([CityLocation, CountryLanguage]))

    @agent.tool_plain
    async def get_user_country() -> str:
        return 'Mexico'

    result = await agent.run('What is the largest city in the user country?')
    assert result.output == snapshot(CityLocation(city='Mexico City', country='Mexico'))

    assert result.all_messages() == snapshot(
        [
            ModelRequest(
                parts=[
                    UserPromptPart(
                        content='What is the largest city in the user country?',
                        timestamp=IsDatetime(),
                    )
                ]
            ),
            ModelResponse(
                parts=[ToolCallPart(tool_name='get_user_country', args='{}', tool_call_id=IsStr())],
                usage=RequestUsage(input_tokens=153, output_tokens=12, details={'reasoning_tokens': 0}),
                model_name='gpt-4o-2024-08-06',
                timestamp=IsDatetime(),
                provider_name='openai',
                provider_details={'finish_reason': 'completed'},
                provider_response_id='resp_68477f10f2d081a39b3438f413b3bafc0dd57d732903c563',
                finish_reason='stop',
            ),
            ModelRequest(
                parts=[
                    ToolReturnPart(
                        tool_name='get_user_country',
                        content='Mexico',
                        tool_call_id='call_UaLahjOtaM2tTyYZLxTCbOaP|fc_68477f1168a081a3981e847cd94275080dd57d732903c563',
                        timestamp=IsDatetime(),
                    )
                ]
            ),
            ModelResponse(
                parts=[
                    TextPart(
                        content='{"result":{"kind":"CityLocation","data":{"city":"Mexico City","country":"Mexico"}}}',
                        id='msg_68477f1235b8819d898adc64709c7ebf061ad97e2eef7871',
                    )
                ],
                usage=RequestUsage(input_tokens=176, output_tokens=26, details={'reasoning_tokens': 0}),
                model_name='gpt-4o-2024-08-06',
                timestamp=IsDatetime(),
                provider_name='openai',
                provider_details={'finish_reason': 'completed'},
                provider_response_id='resp_68477f119830819da162aa6e10552035061ad97e2eef7871',
                finish_reason='stop',
            ),
        ]
    )


@pytest.mark.vcr()
async def test_prompted_output(allow_model_requests: None, openai_api_key: str):
    m = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key=openai_api_key))

    class CityLocation(BaseModel):
        city: str
        country: str

    agent = Agent(m, output_type=PromptedOutput(CityLocation))

    @agent.tool_plain
    async def get_user_country() -> str:
        return 'Mexico'

    result = await agent.run('What is the largest city in the user country?')
    assert result.output == snapshot(CityLocation(city='Mexico City', country='Mexico'))

    assert result.all_messages() == snapshot(
        [
            ModelRequest(
                parts=[
                    UserPromptPart(
                        content='What is the largest city in the user country?',
                        timestamp=IsDatetime(),
                    )
                ],
                instructions="""\
Always respond with a JSON object that's compatible with this schema:

{"properties": {"city": {"type": "string"}, "country": {"type": "string"}}, "required": ["city", "country"], "title": "CityLocation", "type": "object"}

Don't include any text or Markdown fencing before or after.\
""",
            ),
            ModelResponse(
                parts=[ToolCallPart(tool_name='get_user_country', args='{}', tool_call_id=IsStr())],
                usage=RequestUsage(input_tokens=107, output_tokens=12, details={'reasoning_tokens': 0}),
                model_name='gpt-4o-2024-08-06',
                timestamp=IsDatetime(),
                provider_name='openai',
                provider_details={'finish_reason': 'completed'},
                provider_response_id='resp_68482f12d63881a1830201ed101ecfbf02f8ef7f2fb42b50',
                finish_reason='stop',
            ),
            ModelRequest(
                parts=[
                    ToolReturnPart(
                        tool_name='get_user_country',
                        content='Mexico',
                        tool_call_id='call_FrlL4M0CbAy8Dhv4VqF1Shom|fc_68482f1b0ff081a1b37b9170ee740d1e02f8ef7f2fb42b50',
                        timestamp=IsDatetime(),
                    )
                ],
                instructions="""\
Always respond with a JSON object that's compatible with this schema:

{"properties": {"city": {"type": "string"}, "country": {"type": "string"}}, "required": ["city", "country"], "title": "CityLocation", "type": "object"}

Don't include any text or Markdown fencing before or after.\
""",
            ),
            ModelResponse(
                parts=[
                    TextPart(
                        content='{"city":"Mexico City","country":"Mexico"}',
                        id='msg_68482f1c159081918a2405f458009a6a044fdb7d019d4115',
                    )
                ],
                usage=RequestUsage(input_tokens=130, output_tokens=12, details={'reasoning_tokens': 0}),
                model_name='gpt-4o-2024-08-06',
                timestamp=IsDatetime(),
                provider_name='openai',
                provider_details={'finish_reason': 'completed'},
                provider_response_id='resp_68482f1b556081918d64c9088a470bf0044fdb7d019d4115',
                finish_reason='stop',
            ),
        ]
    )


@pytest.mark.vcr()
async def test_prompted_output_multiple(allow_model_requests: None, openai_api_key: str):
    m = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(api_key=openai_api_key))

    class CityLocation(BaseModel):
        city: str
        country: str

    class CountryLanguage(BaseModel):
        country: str
        language: str

    agent = Agent(m, output_type=PromptedOutput([CityLocation, CountryLanguage]))

    @agent.tool_plain
    async def get_user_country() -> str:
        return 'Mexico'

    result = await agent.run('What is the largest city in the user country?')
    assert result.output == snapshot(CityLocation(city='Mexico City', country='Mexico'))

    assert result.all_messages() == snapshot(
        [
            ModelRequest(
                parts=[
                    UserPromptPart(
                        content='What is the largest city in the user country?',
                        timestamp=IsDatetime(),
                    )
                ],
                instructions="""\
Always respond with a JSON object that's compatible with this schema:

{"type": "object", "properties": {"result": {"anyOf": [{"type": "object", "properties": {"kind": {"type": "string", "const": "CityLocation"}, "data": {"properties": {"city": {"type": "string"}, "country": {"type": "string"}}, "required": ["city", "country"], "type": "object"}}, "required": ["kind", "data"], "additionalProperties": false, "title": "CityLocation"}, {"type": "object", "properties": {"kind": {"type": "string", "const": "CountryLanguage"}, "data": {"properties": {"country": {"type": "string"}, "language": {"type": "string"}}, "required": ["country", "language"], "type": "object"}}, "required": ["kind", "data"], "additionalProperties": false, "title": "CountryLanguage"}]}}, "required": ["result"], "additionalProperties": false}

Don't include any text or Markdown fencing before or after.\
""",
            ),
            ModelResponse(
                parts=[ToolCallPart(tool_name='get_user_country', args='{}', tool_call_id=IsStr())],
                usage=RequestUsage(input_tokens=283, output_tokens=12, details={'reasoning_tokens': 0}),
                model_name='gpt-4o-2024-08-06',
                timestamp=IsDatetime(),
                provider_name='openai',
                provider_details={'finish_reason': 'completed'},
                provider_response_id='resp_68482f1d38e081a1ac828acda978aa6b08e79646fe74d5ee',
                finish_reason='stop',
            ),
            ModelRequest(
                parts=[
                    ToolReturnPart(
                        tool_name='get_user_country',
                        content='Mexico',
                        tool_call_id='call_my4OyoVXRT0m7bLWmsxcaCQI|fc_68482f2889d481a199caa61de7ccb62c08e79646fe74d5ee',
                        timestamp=IsDatetime(),
                    )
                ],
                instructions="""\
Always respond with a JSON object that's compatible with this schema:

{"type": "object", "properties": {"result": {"anyOf": [{"type": "object", "properties": {"kind": {"type": "string", "const": "CityLocation"}, "data": {"properties": {"city": {"type": "string"}, "country": {"type": "string"}}, "required": ["city", "country"], "type": "object"}}, "required": ["kind", "data"], "additionalProperties": false, "title": "CityLocation"}, {"type": "object", "properties": {"kind": {"type": "string", "const": "CountryLanguage"}, "data": {"properties": {"country": {"type": "string"}, "language": {"type": "string"}}, "required": ["country", "language"], "type": "object"}}, "required": ["kind", "data"], "additionalProperties": false, "title": "CountryLanguage"}]}}, "required": ["result"], "additionalProperties": false}

Don't include any text or Markdown fencing before or after.\
""",
            ),
            ModelResponse(
                parts=[
                    TextPart(
                        content='{"result":{"kind":"CityLocation","data":{"city":"Mexico City","country":"Mexico"}}}',
                        id='msg_68482f296bfc81a18665547d4008ab2c06b4ab2d00d03024',
                    )
                ],
                usage=RequestUsage(input_tokens=306, output_tokens=22, details={'reasoning_tokens': 0}),
                model_name='gpt-4o-2024-08-06',
                timestamp=IsDatetime(),
                provider_name='openai',
                provider_details={'finish_reason': 'completed'},
                provider_response_id='resp_68482f28c1b081a1ae73cbbee012ee4906b4ab2d00d03024',
                finish_reason='stop',
            ),
        ]
    )


@pytest.mark.vcr()
async def test_openai_responses_verbosity(allow_model_requests: None, openai_api_key: str):
    """Test that verbosity setting is properly passed to the OpenAI API"""
    # Following GPT-5 + verbosity documentation pattern
    provider = OpenAIProvider(
        api_key=openai_api_key,
        base_url='https://api.openai.com/v1',  # Explicitly set base URL
    )
    model = OpenAIResponsesModel('gpt-5', provider=provider)
    agent = Agent(model=model, model_settings=OpenAIResponsesModelSettings(openai_text_verbosity='low'))
    result = await agent.run('What is 2+2?')
    assert result.output == snapshot('4')


async def test_openai_responses_usage_without_tokens_details(allow_model_requests: None):
    c = response_message(
        [
            ResponseOutputMessage(
                id='123',
                content=cast(list[Content], [ResponseOutputText(text='4', type='output_text', annotations=[])]),
                role='assistant',
                status='completed',
                type='message',
            )
        ],
        # Intentionally use model_construct so that input_tokens_details and output_tokens_details will not be set.
        usage=ResponseUsage.model_construct(input_tokens=14, output_tokens=1, total_tokens=15),
    )
    mock_client = MockOpenAIResponses.create_mock(c)
    model = OpenAIResponsesModel('gpt-4o', provider=OpenAIProvider(openai_client=mock_client))

    agent = Agent(model=model)
    result = await agent.run('What is 2+2?')
    assert result.all_messages() == snapshot(
        [
            ModelRequest(
                parts=[
                    UserPromptPart(
                        content='What is 2+2?',
                        timestamp=IsDatetime(),
                    )
                ]
            ),
            ModelResponse(
                parts=[TextPart(content='4', id='123')],
                usage=RequestUsage(input_tokens=14, output_tokens=1, details={'reasoning_tokens': 0}),
                model_name='gpt-4o-123',
                timestamp=IsDatetime(),
                provider_name='openai',
                provider_response_id='123',
            ),
        ]
    )

    assert result.usage() == snapshot(
        RunUsage(input_tokens=14, output_tokens=1, details={'reasoning_tokens': 0}, requests=1)
    )


async def test_openai_responses_model_thinking_part(allow_model_requests: None, openai_api_key: str):
    m = OpenAIResponsesModel('gpt-5', provider=OpenAIProvider(api_key=openai_api_key))
    settings = OpenAIResponsesModelSettings(openai_reasoning_effort='high', openai_reasoning_summary='detailed')
    agent = Agent(m, model_settings=settings)

    result = await agent.run('How do I cross the street?')
    assert result.all_messages() == snapshot(
        [
            ModelRequest(parts=[UserPromptPart(content='How do I cross the street?', timestamp=IsDatetime())]),
            ModelResponse(
                parts=[
                    ThinkingPart(
                        content=IsStr(),
                        id='rs_68c36eafb6f881a3bd47d4f10db61dee033a1f85a7ada5bf',
                        signature=IsStr(),
                        provider_name='openai',
                    ),
                    ThinkingPart(
                        content=IsStr(),
                        id='rs_68c36eafb6f881a3bd47d4f10db61dee033a1f85a7ada5bf',
                    ),
                    ThinkingPart(
                        content=IsStr(),
                        id='rs_68c36eafb6f881a3bd47d4f10db61dee033a1f85a7ada5bf',
                    ),
                    ThinkingPart(
                        content=IsStr(),
                        id='rs_68c36eafb6f881a3bd47d4f10db61dee033a1f85a7ada5bf',
                    ),
                    ThinkingPart(
                        content=IsStr(),
                        id='rs_68c36eafb6f881a3bd47d4f10db61dee033a1f85a7ada5bf',
                    ),
                    TextPart(content=IsStr(), id='msg_68c36ec63adc81a39b63da30b6a85f59033a1f85a7ada5bf'),
                ],
                usage=RequestUsage(input_tokens=13, output_tokens=1918, details={'reasoning_tokens': 1600}),
                model_name='gpt-5-2025-08-07',
                timestamp=IsDatetime(),
                provider_name='openai',
                provider_details={'finish_reason': 'completed'},
                provider_response_id='resp_68c36eaf77d081a39099dbc0fc3bdea9033a1f85a7ada5bf',
                finish_reason='stop',
            ),
        ]
    )

    result = await agent.run(
        'Considering the way to cross the street, analogously, how do I cross the river?',
        message_history=result.all_messages(),
    )
    assert result.new_messages() == snapshot(
        [
            ModelRequest(
                parts=[
                    UserPromptPart(
                        content='Considering the way to cross the street, analogously, how do I cross the river?',
                        timestamp=IsDatetime(),
                    )
                ]
            ),
            ModelResponse(
                parts=[
                    ThinkingPart(
                        content=IsStr(),
                        id='rs_68c36ec8ae5881a3b5e89a47b3ebe438033a1f85a7ada5bf',
                        signature=IsStr(),
                        provider_name='openai',
                    ),
                    ThinkingPart(
                        content=IsStr(),
                        id='rs_68c36ec8ae5881a3b5e89a47b3ebe438033a1f85a7ada5bf',
                    ),
                    ThinkingPart(
                        content=IsStr(),
                        id='rs_68c36ec8ae5881a3b5e89a47b3ebe438033a1f85a7ada5bf',
                    ),
                    ThinkingPart(
                        content=IsStr(),
                        id='rs_68c36ec8ae5881a3b5e89a47b3ebe438033a1f85a7ada5bf',
                    ),
                    ThinkingPart(
                        content=IsStr(),
                        id='rs_68c36ec8ae5881a3b5e89a47b3ebe438033a1f85a7ada5bf',
                    ),
                    ThinkingPart(
                        content=IsStr(),
                        id='rs_68c36ec8ae5881a3b5e89a47b3ebe438033a1f85a7ada5bf',
                    ),
                    TextPart(content=IsStr(), id='msg_68c36f0437e881a38fdf86f8d1db74f2033a1f85a7ada5bf'),
                ],
                usage=RequestUsage(input_tokens=353, output_tokens=3097, details={'reasoning_tokens': 2624}),
                model_name='gpt-5-2025-08-07',
                timestamp=IsDatetime(),
                provider_name='openai',
                provider_details={'finish_reason': 'completed'},
                provider_response_id='resp_68c36ec7742c81a3b82f5b5e6ae48390033a1f85a7ada5bf',
                finish_reason='stop',
            ),
        ]
    )


async def test_openai_responses_thinking_part_from_other_model(
    allow_model_requests: None, anthropic_api_key: str, openai_api_key: str
):
    m = AnthropicModel(
        'claude-sonnet-4-0',
        provider=AnthropicProvider(api_key=anthropic_api_key),
        settings=AnthropicModelSettings(anthropic_thinking={'type': 'enabled', 'budget_tokens': 1024}),
    )
    agent = Agent(m)

    result = await agent.run('How do I cross the street?')
    assert result.all_messages() == snapshot(
        [
            ModelRequest(
                parts=[
                    UserPromptPart(
                        content='How do I cross the street?',
                        timestamp=IsDatetime(),
                    )
                ]
            ),
            ModelResponse(
                parts=[
                    ThinkingPart(
                        content=IsStr(),
                        signature=IsStr(),
                        provider_name='anthropic',
                    ),
                    TextPart(content=IsStr()),
                ],
                usage=RequestUsage(
                    input_tokens=42,
                    output_tokens=278,
                    details={
                        'cache_creation_input_tokens': 0,
                        'cache_read_input_tokens': 0,
                        'input_tokens': 42,
                        'output_tokens': 278,
                    },
                ),
                model_name='claude-sonnet-4-20250514',
                timestamp=IsDatetime(),
                provider_name='anthropic',
                provider_details={'finish_reason': 'end_turn'},
                provider_response_id='msg_01Xb5RvZxDvuvTBVHG7AmQna',
                finish_reason='stop',
            ),
        ]
    )

    result = await agent.run(
        'Considering the way to cross the street, analogously, how do I cross the river?',
        model=OpenAIResponsesModel(
            'gpt-5',
            provider=OpenAIProvider(api_key=openai_api_key),
            settings=OpenAIResponsesModelSettings(openai_reasoning_effort='high', openai_reasoning_summary='detailed'),
        ),
        message_history=result.all_messages(),
    )
    assert result.new_messages() == snapshot(
        [
            ModelRequest(
                parts=[
                    UserPromptPart(
                        content='Considering the way to cross the street, analogously, how do I cross the river?',
                        timestamp=IsDatetime(),
                    )
                ]
            ),
            ModelResponse(
                parts=[
                    ThinkingPart(
                        content=IsStr(),
                        id='rs_68c368ab1038819c84ae1f570b3e050209941cd87a51b324',
                        signature=IsStr(),
                        provider_name='openai',
                    ),
                    ThinkingPart(
                        content=IsStr(),
                        id='rs_68c368ab1038819c84ae1f570b3e050209941cd87a51b324',
                    ),
                    ThinkingPart(
                        content=IsStr(),
                        id='rs_68c368ab1038819c84ae1f570b3e050209941cd87a51b324',
                    ),
                    ThinkingPart(
                        content=IsStr(),
                        id='rs_68c368ab1038819c84ae1f570b3e050209941cd87a51b324',
                    ),
                    ThinkingPart(
                        content=IsStr(),
                        id='rs_68c368ab1038819c84ae1f570b3e050209941cd87a51b324',
                    ),
                    ThinkingPart(
                        content=IsStr(),
                        id='rs_68c368ab1038819c84ae1f570b3e050209941cd87a51b324',
                    ),
                    TextPart(content=IsStr(), id='msg_68c368d519c4819ca1c501002d55d44c09941cd87a51b324'),
                ],
                usage=RequestUsage(input_tokens=295, output_tokens=2778, details={'reasoning_tokens': 2432}),
                model_name='gpt-5-2025-08-07',
                timestamp=IsDatetime(),
                provider_name='openai',
                provider_details={'finish_reason': 'completed'},
                provider_response_id='resp_68c368aa7c4c819c878d6f3c8a02a28609941cd87a51b324',
                finish_reason='stop',
            ),
        ]
    )


async def test_openai_responses_thinking_part_iter(allow_model_requests: None, openai_api_key: str):
    provider = OpenAIProvider(api_key=openai_api_key)
    responses_model = OpenAIResponsesModel('o3-mini', provider=provider)
    settings = OpenAIResponsesModelSettings(openai_reasoning_effort='high', openai_reasoning_summary='detailed')
    agent = Agent(responses_model, model_settings=settings)

    async with agent.iter(user_prompt='How do I cross the street?') as agent_run:
        async for node in agent_run:
            if Agent.is_model_request_node(node) or Agent.is_call_tools_node(node):
                async with node.stream(agent_run.ctx) as request_stream:
                    async for _ in request_stream:
                        pass

    assert agent_run.result is not None
    assert agent_run.result.all_messages() == snapshot(
        [
            ModelRequest(
                parts=[
                    UserPromptPart(
                        content='How do I cross the street?',
                        timestamp=IsDatetime(),
                    )
                ]
            ),
            ModelResponse(
                parts=[
                    ThinkingPart(
                        content=IsStr(),
                        id='rs_68bb4cc9730481a38d9aaf55dff8dd4a0b681c5350c0b73b',
                        signature=IsStr(),
                        provider_name='openai',
                    ),
                    ThinkingPart(content=IsStr(), id='rs_68bb4cc9730481a38d9aaf55dff8dd4a0b681c5350c0b73b'),
                    ThinkingPart(content=IsStr(), id='rs_68bb4cc9730481a38d9aaf55dff8dd4a0b681c5350c0b73b'),
                    TextPart(content=IsStr(), id='msg_68bb4cd204f881a3b7efcb8866b634410b681c5350c0b73b'),
                ],
                usage=RequestUsage(input_tokens=13, output_tokens=1733, details={'reasoning_tokens': 1280}),
                model_name='o3-mini-2025-01-31',
                timestamp=IsDatetime(),
                provider_name='openai',
                provider_details={'finish_reason': 'completed'},
                provider_response_id='resp_68bb4cbe885481a3a55b6a2e6d6aa5120b681c5350c0b73b',
                finish_reason='stop',
            ),
        ]
    )


async def test_openai_responses_thinking_with_tool_calls(allow_model_requests: None, openai_api_key: str):
    provider = OpenAIProvider(api_key=openai_api_key)
    m = OpenAIResponsesModel(
        model_name='gpt-5',
        provider=provider,
        settings=OpenAIResponsesModelSettings(openai_reasoning_summary='detailed', openai_reasoning_effort='low'),
    )
    agent = Agent(model=m)

    @agent.instructions
    def system_prompt():
        return (
            'You are a helpful assistant that uses planning. You MUST use the update_plan tool and continually '
            "update it as you make progress against the user's prompt"
        )

    @agent.tool_plain
    def update_plan(plan: str) -> str:
        return 'plan updated'

    prompt = (
        'Compose a 12-line poem where the first letters of the odd-numbered lines form the name "SAMIRA" '
        'and the first letters of the even-numbered lines spell out "DAWOOD." Additionally, the first letter '
        'of each word in every line should create the capital of a country'
    )

    result = await agent.run(prompt)

    assert result.all_messages() == snapshot(
        [
            ModelRequest(
                parts=[
                    UserPromptPart(
                        content='Compose a 12-line poem where the first letters of the odd-numbered lines form the name "SAMIRA" and the first letters of the even-numbered lines spell out "DAWOOD." Additionally, the first letter of each word in every line should create the capital of a country',
                        timestamp=IsDatetime(),
                    )
                ],
                instructions="You are a helpful assistant that uses planning. You MUST use the update_plan tool and continually update it as you make progress against the user's prompt",
            ),
            ModelResponse(
                parts=[
                    ThinkingPart(
                        content=IsStr(),
                        id='rs_68c301598b5c81938a8f95605519c25a00b441a18c4893c1',
                        signature=IsStr(),
                        provider_name='openai',
                    ),
                    ThinkingPart(
                        content=IsStr(),
                        id='rs_68c301598b5c81938a8f95605519c25a00b441a18c4893c1',
                    ),
                    ThinkingPart(
                        content=IsStr(),
                        id='rs_68c301598b5c81938a8f95605519c25a00b441a18c4893c1',
                    ),
                    ThinkingPart(
                        content=IsStr(),
                        id='rs_68c301598b5c81938a8f95605519c25a00b441a18c4893c1',
                    ),
                    ThinkingPart(
                        content=IsStr(),
                        id='rs_68c301598b5c81938a8f95605519c25a00b441a18c4893c1',
                    ),
                    ToolCallPart(
                        tool_name='update_plan',
                        args=IsStr(),
                        tool_call_id='call_WrCgFeUNTYD3S3yvrY7RFwXM|fc_68c3018f9aa88193952ceab700035b3600b441a18c4893c1',
                    ),
                ],
                usage=RequestUsage(input_tokens=124, output_tokens=2098, details={'reasoning_tokens': 1984}),
                model_name='gpt-5-2025-08-07',
                timestamp=IsDatetime(),
                provider_name='openai',
                provider_details={'finish_reason': 'completed'},
                provider_response_id='resp_68c30157af5c819393a64d8d810d562700b441a18c4893c1',
                finish_reason='stop',
            ),
            ModelRequest(
                parts=[
                    ToolReturnPart(
                        tool_name='update_plan',
                        content='plan updated',
                        tool_call_id='call_WrCgFeUNTYD3S3yvrY7RFwXM|fc_68c3018f9aa88193952ceab700035b3600b441a18c4893c1',
                        timestamp=IsDatetime(),
                    )
                ],
                instructions="You are a helpful assistant that uses planning. You MUST use the update_plan tool and continually update it as you make progress against the user's prompt",
            ),
            ModelResponse(
                parts=[TextPart(content=IsStr(), id='msg_68c3019459f48193a6653ef497bd4c6000b441a18c4893c1')],
                usage=RequestUsage(
                    input_tokens=2272, cache_read_tokens=1152, output_tokens=114, details={'reasoning_tokens': 0}
                ),
                model_name='gpt-5-2025-08-07',
                timestamp=IsDatetime(),
                provider_name='openai',
                provider_details={'finish_reason': 'completed'},
                provider_response_id='resp_68c301935a2881939de9421990d0cd7c00b441a18c4893c1',
                finish_reason='stop',
            ),
        ]
    )


async def test_openai_responses_thinking_without_summary(allow_model_requests: None):
    c = response_message(
        [
            ResponseReasoningItem(
                id='reasoning',
                summary=[],
                type='reasoning',
                encrypted_content='123',
            ),
            ResponseOutputMessage(
                id='text',
                content=cast(list[Content], [ResponseOutputText(text='4', type='output_text', annotations=[])]),
                role='assistant',
                status='completed',
                type='message',
            ),
        ],
    )
    mock_client = MockOpenAIResponses.create_mock(c)
    model = OpenAIResponsesModel('gpt-5', provider=OpenAIProvider(openai_client=mock_client))

    agent = Agent(model=model)
    result = await agent.run('What is 2+2?')
    assert result.all_messages() == snapshot(
        [
            ModelRequest(
                parts=[
                    UserPromptPart(
                        content='What is 2+2?',
                        timestamp=IsDatetime(),
                    )
                ]
            ),
            ModelResponse(
                parts=[
                    ThinkingPart(content='', id='reasoning', signature='123', provider_name='openai'),
                    TextPart(content='4', id='text'),
                ],
                model_name='gpt-4o-123',
                timestamp=IsDatetime(),
                provider_name='openai',
                provider_response_id='123',
            ),
        ]
    )

    _, openai_messages = await model._map_messages(result.all_messages(), model_settings=model.settings or {})  # type: ignore[reportPrivateUsage]
    assert openai_messages == snapshot(
        [
            {'role': 'user', 'content': 'What is 2+2?'},
            {'id': 'reasoning', 'summary': [], 'encrypted_content': '123', 'type': 'reasoning'},
            {'role': 'assistant', 'content': '4'},
        ]
    )


async def test_openai_responses_thinking_with_modified_history(allow_model_requests: None, openai_api_key: str):
    m = OpenAIResponsesModel('gpt-5', provider=OpenAIProvider(api_key=openai_api_key))
    settings = OpenAIResponsesModelSettings(openai_reasoning_effort='low', openai_reasoning_summary='detailed')
    agent = Agent(m, model_settings=settings)

    result = await agent.run('What is the meaning of life?')
    messages = result.all_messages()
    assert result.all_messages() == snapshot(
        [
            ModelRequest(
                parts=[
                    UserPromptPart(
                        content='What is the meaning of life?',
                        timestamp=IsDatetime(),
                    )
                ]
            ),
            ModelResponse(
                parts=[
                    ThinkingPart(
                        content=IsStr(),
                        id='rs_68c36b7dbd58819e8c05f6f1205cf2fc011e2e4dcb20dbb7',
                        signature=IsStr(),
                        provider_name='openai',
                    ),
                    TextPart(content=IsStr(), id='msg_68c36b84180c819e9e4d96c79945b7af011e2e4dcb20dbb7'),
                ],
                usage=RequestUsage(input_tokens=13, output_tokens=509, details={'reasoning_tokens': 192}),
                model_name='gpt-5-2025-08-07',
                timestamp=IsDatetime(),
                provider_name='openai',
                provider_details={'finish_reason': 'completed'},
                provider_response_id='resp_68c36b7d498c819eae7c20d569041316011e2e4dcb20dbb7',
                finish_reason='stop',
            ),
        ]
    )

    response = messages[-1]
    assert isinstance(response, ModelResponse)
    assert isinstance(response.parts, list)
    response.parts[1] = TextPart(content='The meaning of life is 42')

    with pytest.raises(
        ModelHTTPError,
        match="Item 'rs_68c36b7dbd58819e8c05f6f1205cf2fc011e2e4dcb20dbb7' of type 'reasoning' was provided without its required following item.",
    ):
        await agent.run('Anything to add?', message_history=messages)

    result = await agent.run(
        'Anything to add?',
        message_history=messages,
        model_settings=OpenAIResponsesModelSettings(
            openai_reasoning_effort='low',
            openai_reasoning_summary='detailed',
            openai_send_reasoning_ids=False,
        ),
    )
    assert result.new_messages() == snapshot(
        [
            ModelRequest(
                parts=[
                    UserPromptPart(
                        content='Anything to add?',
                        timestamp=IsDatetime(),
                    )
                ]
            ),
            ModelResponse(
                parts=[
                    ThinkingPart(
                        content=IsStr(),
                        id='rs_68c36b87d894819ca6af6d79c43c61e10f165aa9d4aec1a3',
                        signature=IsStr(),
                        provider_name='openai',
                    ),
                    TextPart(content=IsStr(), id='msg_68c36b8c0bc0819ca376f8e5b44025010f165aa9d4aec1a3'),
                ],
                usage=RequestUsage(input_tokens=172, output_tokens=419, details={'reasoning_tokens': 128}),
                model_name='gpt-5-2025-08-07',
                timestamp=IsDatetime(),
                provider_name='openai',
                provider_details={'finish_reason': 'completed'},
                provider_response_id='resp_68c36b876578819ca92f2de1060797e80f165aa9d4aec1a3',
                finish_reason='stop',
            ),
        ]
    )
