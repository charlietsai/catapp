####################################################################################################
# RUN PYLINT AND NOSETESTS
# - requires that DEV_PATH is an environment variable
#
# USAGE:
# - validate_source.sh [optional source directory, defaults to catapp/catapp-web]
####################################################################################################

#...................................................................................................
# CONFIGURATION
#...................................................................................................
SOURCE_DIR=${DEV_PATH}/${1:-catapp/catapp-web}
LOG_FILE=/tmp/source_validation.log
SUMMARY_FILE=/tmp/source_validation_summary.log
SOURCE_FILES=$(find ${SOURCE_DIR} -name "*py")
TEST_FILES=$(find ${SOURCE_DIR} -name "test_*.py")
PYLINT_DISABLE_FOR_TESTS=(-d no-self-use
                          -d invalid-name
                          -d protected-access
                          -d redefined-builtin
                          -d unused-argument
                          -d too-many-public-methods
                          -d too-many-arguments
                          -d arguments-differ
                          -d no-value-for-parameter)  # sometimes the case if mocking 

#...................................................................................................
# SETUP
#...................................................................................................
rm -f $LOG_FILE
rm -f $SUMMARY_FILE
function log {
    echo $1 | tee -a $LOG_FILE
}
function summary {
    echo $1 "SUMMARY" >> $SUMMARY_FILE
    tail -n $2 ${LOG_FILE} >> $SUMMARY_FILE
}
cd ${SOURCE_DIR}/..  # do this to find .coveragerc


#...................................................................................................
# VALIDATION
#...................................................................................................
log ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"
log "VALIDATING SOURCE"
log ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>"

log "RUNNING PYLINT ON ${SOURCE_DIR} (SOURCE AND DEMOS)"
pylint -j 0 --rcfile=pylintrc ${SOURCE_FILES} | tee -a ${LOG_FILE}
summary "PYLINT (SOURCE AND DEMOS)" 4

log "RUNNING PYLINT ON ${SOURCE_DIR} (TESTS)"
pylint -j 0 --rcfile=pylintrc ${TEST_FILES} ${PYLINT_DISABLE_FOR_TESTS[*]} | tee -a ${LOG_FILE}
summary "PYLINT (TESTS)" 4

log "RUNNING NOSETESTS ${SOURCE_DIR} WITH OPTIONS ${NOSE_OPTIONS}"
nosetests --with-coverage --cover-erase --cover-inclusive --cover-package=${SOURCE_DIR} \
    --ignore-files=${IGNORED_FILES} -a '!network' ${SOURCE_DIR} 2>&1 \
    | tee -a ${LOG_FILE}
summary "NOSETESTS UNDER PYTHON" 5

#...................................................................................................
# TEARDOWN
#...................................................................................................
# clear
cat $SUMMARY_FILE
cd - > /dev/null
