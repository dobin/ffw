
all: requirements 

requirements:
	mkdir bin corpus crashes temp verified

compile:
	cd src; make HFUZZ_CC_ASAN="true" CC="/Development/honggfuzz/hfuzz_cc/hfuzz-clang"
	cp src/vulnserver_hfuzz bin/

fuzz:
	python /ffw/ffw.py --config config.py --basedir /ffw --honggmode

clear:
	rm -rf bin/*.fuzz
	rm -rf bin/HONGGFUZZ.REPORT.TXT
	rm -rf bin/HF_SANCOV
	rm -rf bin/HF.sanitizer.log.*
	rm -f corpus/* crashes/* verified/*
