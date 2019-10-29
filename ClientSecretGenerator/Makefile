build_all:
	mvn clean package
	rm -fr dist
	mkdir dist
	cp target/ClientSecretGenerator-1.0.0-SNAPSHOT-jar-with-dependencies.jar dist/SiwaClientSecretGenerator.jar
	cp README.md dist/README.md