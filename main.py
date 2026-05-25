from openai import OpenAI

from context import Context
from modelConnection import LocalModelFactory, CloudModelFactory
from primitiveTools import ToolRegistry
from plan import Plan
from enums import *
import consts


if __name__ == '__main__':
    cloudmodelPicker = input("pick cloud model: ")
    cloudLLM = CloudModelFactory(cloudmodelPicker)

    privatmodelPicker = input("pick private model: ")
    privateLLM = LocalModelFactory(privatmodelPicker)

    tool_registry = ToolRegistry()
    local_tools_description = tool_registry.get_available_tools()

    planContext = Context()
    pln = Plan(consts.plan_prompt)

    plan_flag = False
    user_input = input("write your input here: ")

    while not plan_flag:
        if pln.is_first_prompt():
            plan_p = pln.prompt(user_input, local_tools_description)
            planContext.append('user', plan_p)
        else:
            planContext.append('user', user_input)

        chat = planContext.getContextList()
        cloud_plan = cloudLLM.chat(chat, reasoning=cloudLLM.REASONING.NONE)

        pln.set_plan(cloud_plan)

        planContext.append('assistant', cloud_plan)
        print(cloud_plan)

        user_input = input("write your input here: ")

        if user_input == "END":
            plan_flag = True