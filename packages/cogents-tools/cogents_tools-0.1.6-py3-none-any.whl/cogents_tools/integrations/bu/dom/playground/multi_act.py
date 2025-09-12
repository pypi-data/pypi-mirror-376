from cogents_tools.integrations.bu import Agent
from cogents_tools.integrations.bu.browser import BrowserProfile, BrowserSession
from cogents_tools.integrations.bu.browser.types import ViewportSize
from cogents_tools.integrations.llm import get_llm_client_bu_compatible

# Initialize the Azure OpenAI client
llm = get_llm_client_bu_compatible()


TASK = """
Go to https://browser-use.github.io/stress-tests/challenges/react-native-web-form.html and complete the React Native Web form by filling in all required fields and submitting.
"""


async def main():
    browser = BrowserSession(
        browser_profile=BrowserProfile(
            window_size=ViewportSize(width=1100, height=1000),
        )
    )

    agent = Agent(task=TASK, llm=llm)

    await agent.run()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
