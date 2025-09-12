from plumbum import local

# Define the squeue format to include only necessary fields
SQUEUE_FORMAT = "--format=%.18i %.20P %.20j %.20u %.2t %.10M %.10l %.34R %D %L"

# Functions to interact with Slurm commands
# Define the sinfo format to include only necessary fields
SINFO_FORMAT = "--format=%.20P %.6D %.10t"


# Function to retrieve Slurm partition information


def sinfo():
    """
    Retrieve information about Slurm partitions.

    :return: A list of dictionaries, each containing information about a particular Slurm partition.
    """
    sinfo_return = local.cmd.sinfo[SINFO_FORMAT]()
    sinfo_parsed = parse_sinfo_output(sinfo_return)
    for partition in sinfo_parsed:
        total = 0
        for key in partition.keys() - {"PARTITION"}:
            try:
                total += int(partition[key])
            except ValueError:
                print(f"Value {partition[key]} of {key} cannot be converted to integer")
        partition["total"] = total
    return sinfo_parsed


def squeue(me=True):
    """
    Retrieve the list of jobs currently in the Slurm queue.

    :param me: Boolean flag to filter jobs for the current user.
    :return: A list of dictionaries, each containing information about a particular job in the Slurm queue.
    """
    args = "--me" if me else ""
    squeue_return = local.cmd.squeue[SQUEUE_FORMAT, args]()
    return parse_squeue_output(squeue_return)


def parse_sinfo_output(output):
    lines = output.splitlines()

    info = {}
    for line in lines[1:]:
        split = line.split()
        partition = split[0].strip(" *")
        nodes = split[1].strip("* ")
        status = split[2].strip("* ")
        if partition in info:
            try:
                info[partition][status] = int(nodes)
            except ValueError:
                info[partition][status] = nodes

        else:
            info[partition] = {"PARTITION": partition, status: nodes}

    info = list(info.values())
    info.sort(key=lambda x: x["PARTITION"])

    return info


def parse_squeue_output(output):
    """
    Parse the output of the squeue command.

    :param output: The raw output from the squeue command.
    :return: A list of dictionaries, each containing information about a particular job in the Slurm queue.
    """
    lines = output.splitlines()
    headers = lines[0].split()
    jobs = []
    for line in lines[1:]:
        values = line.split()
        job = dict(zip(headers, values))
        jobs.append(job)
    return jobs


def scancel(job_id):
    """
    Cancel a job using its job ID.

    :param job_id: The ID of the job to cancel.
    :return: True if the job was successfully cancelled, False otherwise.
    """
    try:
        local.cmd.scancel[job_id]()
        return True
    except Exception as e:
        print(f"Failed to cancel job {job_id}: {e}")
        return False


def sacct(job_id):
    """
    Retrieve information about a specific job using its job ID.

    :param job_id: The ID of the job to retrieve information for.
    :return: A dictionary containing information about the job.
    """
    try:
        sacct_return = local.cmd.sacct[
            "-X", "--jobs", job_id, "--format=JobID,State,Elapsed,ExitCode"
        ]()
        print(sacct_return)
        return parse_sacct_output(sacct_return)
    except Exception as e:
        print(f"Failed to retrieve job {job_id}: {e}")
        return None


def parse_sacct_output(output):
    """
    Parse the output of the squeue command.

    :param output: The raw output from the squeue command.
    :return: A list of dictionaries, each containing information about a particular job in the Slurm queue.
    """
    lines = output.splitlines()
    headers = lines[0].split()
    jobs = []
    for line in lines[2:]:
        values = line.split()
        job = dict(zip(headers, values))
        jobs.append(job)
    return jobs


if __name__ == "__main__":
    print(squeue())
    print(sinfo())
    # Example usage of sacct
    print(sacct("12345"))
