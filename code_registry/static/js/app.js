document.addEventListener('alpine:init', () => {
    Alpine.data('app', () => ({
        darkMode: window.matchMedia('(prefers-color-scheme: dark)').matches,
        sidebarOpen: window.innerWidth >= 768,
        view: 'repos',
        loading: false,

        // Repos
        repos: [],
        repoFilter: '',
        selectedRepo: null,
        repoDetail: null,
        expandedGroups: {},

        // PRs (loaded lazily)
        prs: null,
        prsLoading: false,
        prsLoadedFor: null,

        // Docs
        docTrees: [],
        flatDocTree: [],
        expandedDirs: {},
        docHtml: null,
        docName: null,
        docPath: null,
        selectedDoc: null,

        init() {
            this.loadRepos();
        },

        get filteredRepos() {
            const q = this.repoFilter.toLowerCase().trim();
            if (!q) return this.repos;
            return this.repos.filter(r => r.toLowerCase().includes(q));
        },

        get repoTree() {
            const repos = this.filteredRepos;
            const grouped = [];
            const ungrouped = [];

            for (const repo of repos) {
                const slashIdx = repo.lastIndexOf('/');
                if (slashIdx === -1) {
                    ungrouped.push(repo);
                } else {
                    grouped.push(repo);
                }
            }

            const nodes = [];
            let lastGroup = null;
            for (const repo of grouped) {
                const slashIdx = repo.lastIndexOf('/');
                const group = repo.substring(0, slashIdx);
                const name = repo.substring(slashIdx + 1);
                if (group !== lastGroup) {
                    nodes.push({ type: 'group', name: group, key: 'g:' + group });
                    lastGroup = group;
                }
                nodes.push({ type: 'repo', name: name, key: repo, group: group });
            }
            for (const repo of ungrouped) {
                nodes.push({ type: 'repo', name: repo, key: repo, group: null });
            }
            return nodes;
        },

        get visibleRepoNodes() {
            const filtering = this.repoFilter.trim().length > 0;
            return this.repoTree.filter(node => {
                if (node.type === 'group') return true;
                if (!node.group) return true;
                return filtering || !!this.expandedGroups[node.group];
            });
        },

        toggleGroup(group) {
            this.expandedGroups[group] = !this.expandedGroups[group];
        },

        get visibleDocNodes() {
            return this.flatDocTree.filter(node => {
                if (node.depth === 0) return true;
                let parent = node.parentPath;
                while (parent) {
                    if (!this.expandedDirs[parent]) return false;
                    const parentNode = this.flatDocTree.find(n => n.path === parent);
                    parent = parentNode ? parentNode.parentPath : null;
                }
                return true;
            });
        },

        toggleDir(path) {
            this.expandedDirs[path] = !this.expandedDirs[path];
        },

        async loadRepos() {
            this.loading = true;
            try {
                const res = await fetch('/api/repos');
                const data = await res.json();
                this.repos = data.repos;
            } catch (e) {
                console.error('Failed to load repos:', e);
            }
            this.loading = false;
        },

        async selectRepo(name) {
            if (window.innerWidth < 768) this.sidebarOpen = false;
            this.selectedRepo = name;
            this.repoDetail = null;
            this.prs = null;
            this.prsLoadedFor = null;
            this.loading = true;
            try {
                const encodedPath = name.split('/').map(encodeURIComponent).join('/');
                const res = await fetch(`/api/repos/${encodedPath}`);
                this.repoDetail = await res.json();
            } catch (e) {
                console.error('Failed to load repo:', e);
            }
            this.loading = false;
        },

        async loadPRs(repoName) {
            if (this.prsLoadedFor === repoName) return;
            this.prsLoading = true;
            this.prs = null;
            try {
                const encodedPath = repoName.split('/').map(encodeURIComponent).join('/');
                const res = await fetch(`/api/repos/${encodedPath}/prs`);
                const data = await res.json();
                this.prs = data.pull_requests;
                this.prsLoadedFor = repoName;
            } catch (e) {
                console.error('Failed to load PRs:', e);
                this.prs = [];
            }
            this.prsLoading = false;
        },

        switchToDocs() {
            this.view = 'docs';
            if (this.docTrees.length === 0) {
                this.loadDocTree();
            }
        },

        async loadDocTree() {
            this.loading = true;
            try {
                const res = await fetch('/api/docs/tree');
                const data = await res.json();
                this.docTrees = data.trees;
                this.flatDocTree = [];
                this.expandedDirs = {};
                for (const tree of data.trees) {
                    this._flattenTree(tree, 0, null);
                }
            } catch (e) {
                console.error('Failed to load doc tree:', e);
            }
            this.loading = false;
        },

        _flattenTree(node, depth, parentPath) {
            this.flatDocTree.push({
                type: node.type,
                name: node.name,
                path: node.path,
                depth: depth,
                parentPath: parentPath,
            });
            if (node.type === 'directory' && node.children) {
                for (const child of node.children) {
                    this._flattenTree(child, depth + 1, node.path);
                }
            }
        },

        async selectDoc(path) {
            if (window.innerWidth < 768) this.sidebarOpen = false;
            this.selectedDoc = path;
            this.loading = true;
            this.docHtml = null;
            try {
                const res = await fetch(`/api/docs/render?path=${encodeURIComponent(path)}`);
                const data = await res.json();
                this.docHtml = data.html;
                this.docName = data.name;
                this.docPath = data.path;
            } catch (e) {
                console.error('Failed to render doc:', e);
            }
            this.loading = false;
        },
    }));
});
