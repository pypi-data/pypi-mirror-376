codes = {
    "cpu_fcfs": """def fcfs(processes, burst_time, arrival_time=None):
    n = len(processes)
    if arrival_time is None:
        arrival_time = [0] * n

    completion_time = [0] * n
    waiting_time = [0] * n
    turnaround_time = [0] * n

    time = 0
    for i in range(n):
        if time < arrival_time[i]:
            time = arrival_time[i]  # CPU idle
        time += burst_time[i]
        completion_time[i] = time
        turnaround_time[i] = completion_time[i] - arrival_time[i]
        waiting_time[i] = turnaround_time[i] - burst_time[i]

    print("PID | AT | BT | CT | TAT | WT")
    for i in range(n):
        print(f"{processes[i]:3} | {arrival_time[i]:2} | {burst_time[i]:2} | {completion_time[i]:2} | {turnaround_time[i]:3} | {waiting_time[i]:2}")

    print("Avg WT =", sum(waiting_time)/n)
    print("Avg TAT =", sum(turnaround_time)/n)
"""
}

def topics():
    return list(codes.keys())

def get_text(name):
    return codes.get(name, "Topic not found")
