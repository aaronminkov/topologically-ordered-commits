# Topologically Ordered Commits
A script to topologically order all commits in a Git repository.

The script:
1. Locates the .git directory.
2. Obtains the list of local branch names.
3. Builds the commit graph. Each commit is represented as an instance of the CommitNode class.
4. Generates a topological ordering of the commits in the graph.
5. Prints the commit hashes in the order generated by the previous step, from least to the greatest.
