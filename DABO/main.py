from context import Context
from modelConnection import LocalModelFactory, CloudModelFactory
from plan import Plan
from enums import *
import consts

if __name__ == '__main__':
    cloudmodelPicker = input("pick cloud model: ") # create the right prompt in prompts class
    cloudLLM = CloudModelFactory(cloudmodelPicker)
    privatmodelPicker = input("pick private model: ") #create the right prompt in prompts class
    privateLLM = LocalModelFactory(privatmodelPicker)
    planContext = Context()
    pln = Plan(consts.plan_prompt)

    plan_flag = False
    user_input = input("write your input here: ")

    while not plan_flag:
        if pln.is_first_prompt():
            plan_p = pln.prompt(user_input)
            planContext.append('user',plan_p)
        else:
            planContext.append('user', user_input)

        chat = planContext.getContextList()
        cloud_plan = cloudLLM.chat(chat, reasoning=REASONING.NONE)
        planContext.append('system', cloud_plan)
        print(cloud_plan)
        user_input = input("write your input here: ")
        if user_input == "END":
            plan_flag = True



