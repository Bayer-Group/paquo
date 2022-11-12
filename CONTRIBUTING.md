# Contribution Guidelines


## Pull requests are always welcome

We're trying very hard to keep our systems simple, lean and focused. We don't
want them to be everything for everybody. This means that we might decide
against incorporating a new request.


## Create issues...

Any significant change should be documented as a GitHub issue before anybody
starts working on it.

### ...but check for existing issues first!

Please take a moment to check that an issue doesn't already exist documenting
your request. If it does, it never hurts to add a quick "+1" or
"I need this too". This will help prioritize the most common requests.


## Conventions

Fork the repository and make changes on your fork on a branch:

1. Create the right type of issue (defect, enhancement, test, etc)
2. Name the branch N-something where N is the number of the issue.

Note that the maintainers work on branches in this repository.

Work hard to ensure your pull request is valid. This includes code quality,
clear naming, and including unit tests. Please read the Code Of Conduct at the
bottom of this file.

Pull request descriptions should be as clear as possible and include a reference
to all the issues that they address. In GitHub, you can reference an issue by
adding a line to your commit description that follows the format:

  `Fixes #N`

where N is the issue number.


## Merge approval

Repository maintainers will review the pull request and make sure it provides
the appropriate level of code quality & correctness.


## How are decisions made?

Short answer: with pull requests to this repository.

All decisions, big and small, follow the same 3 steps:

1. Open a pull request. Anyone can do this.
2. Discuss the pull request. Anyone can do this.
3. Accept or refuse a pull request. The relevant maintainers do this (see below
   "Who decides what?")

   1. Accepting pull requests
      1. If the pull request appears to be ready to merge, approve it.

      2. If the pull request has some small problems that need to be changed,
         make a comment addressing the issues.

      3. If the changes needed to a PR are small, you can add a "LGTM once the
         following comments are addressed..." this will reduce needless back and
         forth.

      4. If the PR only needs a few changes before being merged, any MAINTAINER
         can make a replacement PR that incorporates the existing commits and
         fixes the problems before a fast track merge.

   2. Closing pull requests
      1. If a PR appears to be abandoned, after having attempted to contact the
         original contributor, then a replacement PR may be made. Once the
         replacement PR is made, any contributor may close the original one.

      2. If you are not sure if the pull request implements a good feature or
         you do not understand the purpose of the PR, ask the contributor to
         provide more documentation. If the contributor is not able to
         adequately explain the purpose of the PR, the PR may be closed by any
         MAINTAINER.

      3. If a MAINTAINER feels that the pull request is sufficiently
         architecturally flawed, or if the pull request needs significantly more
         design discussion before being considered, the MAINTAINER should close
         the pull request with a short explanation of what discussion still
         needs to be had. It is important not to leave such pull requests open,
         as this will waste both the MAINTAINER's time and the contributor's
         time. It is not good to string a contributor on for weeks or months,
         having them make many changes to a PR that will eventually be rejected.


## Who decides what?

All decisions are pull requests, and the relevant maintainers make decisions by
accepting or refusing pull requests. Review and acceptance by anyone is denoted
by adding a comment in the pull request: `LGTM`. However, only currently listed
`MAINTAINERS` are counted towards the required majority.

The maintainers will be listed in the MAINTAINER file, all these people will be
in the employment of Bayer.


## I'm a maintainer, should I make pull requests too?

Yes. Nobody should ever push to main directly. All changes should be made
through a pull request.

## Code Of Conduct

As contributors and maintainers of this project, we pledge to respect all people
who contribute through reporting issues, posting feature requests, updating
documentation, submitting pull requests or patches, and other activities.

We are committed to making participation in this project a harassment-free
experience for everyone, regardless of level of experience, gender, gender
identity and expression, sexual orientation, disability, personal appearance,
body size, race, ethnicity, age, or religion.

Examples of unacceptable behavior by participants include the use of sexual
language or imagery, derogatory comments or personal attacks, trolling, public
or private harassment, insults, or other unprofessional conduct.

Project maintainers have the right and responsibility to remove, edit, or reject
comments, commits, code, wiki edits, issues, and other contributions that are
not aligned to this Code of Conduct. Project maintainers who do not follow the
Code of Conduct may be removed from the project team.

Instances of abusive, harassing, or otherwise unacceptable behavior may be
reported by opening an issue or contacting one or more of the project
maintainers.

This Code of Conduct is adapted from the Contributor Covenant, version 1.0.0,
available at
[https://www.contributor-covenant.org/version/1/0/0/code-of-conduct.html][v1]

[v1]: https://www.contributor-covenant.org/version/1/0/0/code-of-conduct.html
