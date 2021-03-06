# vim-sovereign

Gain sovereignty over subversion.


# Design

vim-sovereign allows you to manage your svn checkout as vim intended. Get a
status buffer with `:Sstatus` and add files to a pending submit changlist.
Submit them with `:Scommit -v` and see a diff of those changes while
writing your commit message.


# Requirements

## Python

Python 3 and module svn

```
pip install -r requirements.txt
```

## Optional: [vim-diffusable](https://github.com/idbrii/vim-diffusable)

diff mode is disabled in right and left side when either window is closed. (No more dangling diff windows.)


# License

MIT
