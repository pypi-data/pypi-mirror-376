

###############################################################################
## External support
###############################################################################


###############################################################################
## Add git branch and abbreviated git commit hash to git.hpp header file
###############################################################################
# Get the latest abbreviated commit hash of the working branch
# and force a cmake reconfigure
if (ASGARD_USE_GITINFO)
  include(contrib/GetGitRevisionDescription.cmake)
  get_git_head_revision(GIT_REFSPEC GIT_COMMIT_HASH)
endif()
# Get the current working branch
execute_process(
  COMMAND git rev-parse --abbrev-ref HEAD
  WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
  OUTPUT_VARIABLE GIT_BRANCH
  OUTPUT_STRIP_TRAILING_WHITESPACE
)
# Get the summary of the last commit
execute_process(
  COMMAND git log -n 1 --format="\\n  Date: %ad\\n      %s"
  WORKING_DIRECTORY ${CMAKE_SOURCE_DIR}
  OUTPUT_VARIABLE GIT_COMMIT_SUMMARY
  OUTPUT_STRIP_TRAILING_WHITESPACE
)
# Replace newlines with '\n\t' literal
string(REGEX REPLACE "(\r?\n)+"
       "\\\\n" GIT_COMMIT_SUMMARY
       "${GIT_COMMIT_SUMMARY}"
)
# Remove double quotes
string(REGEX REPLACE "\""
       "" GIT_COMMIT_SUMMARY
       "${GIT_COMMIT_SUMMARY}"
)
