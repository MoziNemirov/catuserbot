import io
import sys
import traceback

from . import catub, edit_or_reply

plugin_category = "utils"


@catub.cat_cmd(
    pattern="calc ([\s\S]*)",
    command=("calc", plugin_category),
    info={
        "заголовок": "Решать элементарные математические уравнения.",
        "описание": "Решает данное математическое уравнение по правилу BODMAS.",
        "Применение": "{tr}calc 2+9",
    },
)
async def calculator(event):
    "Решать элементарные математические уравнения."
    cmd = event.text.split(" ", maxsplit=1)[1]
    event = await edit_or_reply(event, "Calculating ...")
    old_stderr = sys.stderr
    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    redirected_error = sys.stderr = io.StringIO()
    stdout, stderr, exc = None, None, None
    san = f"print({cmd})"
    try:
        await aexec(san, event)
    except Exception:
        exc = traceback.format_exc()
    stdout = redirected_output.getvalue()
    stderr = redirected_error.getvalue()
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    evaluation = ""
    if exc:
        evaluation = exc
    elif stderr:
        evaluation = stderr
    elif stdout:
        evaluation = stdout
    else:
        evaluation = "Извините, я не могу найти результат для данного уравнения"
    final_output = "**УРАВНЕНИЕ**: `{}` \n\n **РЕШЕНИЕ**: \n`{}` \n".format(
        cmd, evaluation
    )
    await event.edit(final_output)


async def aexec(code, event):
    exec("async def __aexec(event): " + "".join(f"\n {l}" for l in code.split("\n")))

    return await locals()["__aexec"](event)
