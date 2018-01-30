import time
import json

def resolve_ctf_template(ctf, title, template_file, solves_template_file):
    with open(template_file, "r") as f:
        template_data = f.read()

    with open(solves_template_file, "r") as f:
        solve_template_data = f.read()

    challenge_data = []

    for challenge in filter(lambda c: c.is_solved, ctf.challenges):
        chall_value = solve_template_data

        chall_value = chall_value.replace("{name}", challenge.name)
        chall_value = chall_value.replace("{solver}", ", ".join(challenge.solver))
        chall_value = chall_value.replace("{solve_date}", time.ctime(challenge.solve_date))
        chall_value = chall_value.replace("{category}", challenge.category if challenge.category else "")

        chall_value = chall_value.replace("{name_with_category}", "{}{}".format(
            challenge.name, " ({})".format(challenge.category) if challenge.category else ""))

        challenge_data.append(chall_value)

    template_data = template_data.replace("{title}", title)
    template_data = template_data.replace("{name}", ctf.name)
    template_data = template_data.replace("{date_now}", time.ctime(time.time()))
    template_data = template_data.replace("{challenges}", "".join(challenge_data))

    return template_data

def resolve_stats_template(ctf):
    stats = {}

    stats["ctfname"] = ctf.name
    stats["challenges"] = []

    for challenge_obj in filter(lambda c: c.is_solved, ctf.challenges):
        challenge = {}

        challenge["name"] = challenge_obj.name
        challenge["solver"] = challenge_obj.solver
        challenge["solve_date"] = challenge_obj.solve_date
        challenge["category"] = challenge_obj.category

        stats["challenges"].append(challenge)

    return json.dumps(stats)
