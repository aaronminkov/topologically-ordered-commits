import os
import sys
import zlib

class CommitNode:
    def __init__(self, commit_hash):
        """
        :type commit_hash: str
        """
        self.commit_hash = commit_hash
        self.parents = set()
        self.children = set()

def topo_order_commits():
    # find the .git directory
    git_dir = find_git_dir()
    branch_path = git_dir+"/.git/refs/heads"

    # recursively create local_branch_list
    local_branch_list = list()
    find_branch_names(branch_path, branch_path, local_branch_list)

    # create a list of commit hashes and make a dict with hashes as keys & branches as values
    (commit_hash_list, head_to_branches) = get_commit_hash(branch_path, local_branch_list)
    (commit_nodes, root_hashes) = build_commit_graph(git_dir, commit_hash_list)

    # order the commits into an ordered list, then print the commits with branch names
    ordered_commits = get_topo_ordered_commits(commit_nodes, root_hashes)
    print_topo_ordered_commits_with_branch_names(commit_nodes, ordered_commits, head_to_branches)

def find_git_dir():
    curr_dir = os.getcwd()
    path = curr_dir+"/.git"

    # if current dirrectory contains .git, return
    if os.path.isdir(path) and os.access(path, os.R_OK):
        return curr_dir
    # now if current directory is /, we know to return
    if curr_dir == '/':
        sys.stderr.write("Not inside a Git repository")
        exit(1)

    # examine each parent directory for .git
    while True:
        curr_dir = os.path.dirname(curr_dir)
        path = curr_dir+"/.git"
        # if current dirrectory contains .git, return
        if os.path.isdir(path) and os.access(path, os.R_OK):
            return curr_dir
        if curr_dir == "/":
            sys.stderr.write("Not inside a Git repository")
            exit(1)

def find_branch_names(dir, branch_path, local_branch_names):
    # For every file within the given directory (dir), add to
    # local_branch_names if it's a file, or use recursion to
    # search if it's a directory.
    for file_n in os.scandir(dir):
        file_name = os.path.relpath(file_n.path, branch_path)
        if file_n.is_file():
            local_branch_names.append(file_name)
        elif file_n.is_dir():
            find_branch_names(file_n.path, branch_path, local_branch_names)

def get_commit_hash(branch_path, local_branch_list):
    commit_hash_list = []
    head_to_branches = {}
    for item in local_branch_list:
        git_file = open(branch_path+"/"+item, 'r')
        curr_hash = git_file.read().rstrip()
        if curr_hash in head_to_branches.keys():
            head_to_branches[curr_hash].append(item)
        else:
            head_to_branches.update({curr_hash: [item]})
        commit_hash_list.append(curr_hash)
    return commit_hash_list, head_to_branches

def get_parents(path, hash):
    parents = []
    parent_commit = zlib.decompress(open(path + "/.git/objects/" + hash[:2] + '/' + hash[2:], 'rb').read())
    parent_commit = parent_commit.decode().splitlines()
    for line in sorted(parent_commit):
        if "parent" in line:
            parent_hash = line.split()[1]
            parents.append(parent_hash)
    return parents


def build_commit_graph(path, hash_list):
    commit_nodes = {}
    root_hashes = []
    visited = set()
    stack = hash_list
    while stack:
        commit_hash = stack.pop()
        if commit_hash in visited:
            continue
        visited.add(commit_hash)
        if commit_hash not in commit_nodes.keys():
            commit_node = CommitNode(commit_hash)
            commit_nodes.update({commit_hash: commit_node})
        else:
            commit_node = commit_nodes[commit_hash]
        parents = get_parents(path, commit_hash)
        for each in sorted(parents):
            commit_node.parents.add(each)
            if each not in visited:
                stack.append(each)
            if each not in commit_nodes.keys():
                parent_node = CommitNode(each)
                commit_nodes.update({each: parent_node})
            commit_nodes[each].children.add(commit_hash)
        if not commit_node.parents:
            root_hashes.append(commit_node.commit_hash)
        commit_nodes[commit_hash] = commit_node
    return commit_nodes, root_hashes

def get_topo_ordered_commits(commit_nodes, root_hashes):
    order = []
    visited = set()
    temp_stack = []
    stack = sorted(root_hashes)
    while stack:
        v = stack.pop()
        if v in visited:
            continue
        visited.add(v)
        while temp_stack and v not in commit_nodes[temp_stack[-1]].children:
            g = temp_stack.pop()
            order.append(g)
        temp_stack.append(v)
        for c in sorted(commit_nodes[v].children):
            if c in visited:
                continue
            stack.append(c)
    while temp_stack:
        order.append(temp_stack.pop())
    return order

def print_topo_ordered_commits_with_branch_names(commit_nodes, topo_ordered_commits, head_to_branches):
    jumped = False
    for i in range(len(topo_ordered_commits)):
        commit_hash = topo_ordered_commits[i]
        if jumped:
            jumped = False
            sticky_hash = ' '.join(commit_nodes[commit_hash].children)
            print(f'={sticky_hash}')
        branches = sorted(head_to_branches[commit_hash]) if commit_hash in head_to_branches else []
        print(commit_hash + (' ' + ' '.join(branches) if branches else ''))
        if i+1 < len(topo_ordered_commits) and topo_ordered_commits[i+1] not in commit_nodes[commit_hash].parents:
            jumped = True
            sticky_hash = ' '.join(commit_nodes[commit_hash].parents)
            print(f'{sticky_hash}=\n')

if __name__ == '__main__':
    topo_order_commits()
