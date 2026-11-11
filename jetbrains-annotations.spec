Name:		jetbrains-annotations
Version:	26.1.0
Release:	2
Summary:	Nullability and API-contract annotations
Group:		Development/Java
License:	Apache-2.0
URL:		https://github.com/JetBrains/java-annotations
# The git tag ships gradle/wrapper/gradle-wrapper.jar. That prebuilt
# wrapper is removed from this archive, and %prep deletes it if it
# comes back. commonMain is Kotlin and is not compiled.
Source0:	https://github.com/JetBrains/java-annotations/archive/refs/tags/%{version}.tar.gz#/jetbrains-annotations-%{version}.tar.gz
# Gradle 9.9.1 strictly pins 24.0.1. The wrapper jar is not in this archive.
Source1:	https://github.com/JetBrains/java-annotations/archive/refs/tags/24.0.1.tar.gz#/jetbrains-annotations-24.0.1.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar

%description
JetBrains annotations document nullability and API contracts for JVM
languages. 26.1.0 is the current release. Gradle 9.9.1 strictly pins
org.jetbrains:annotations 24.0.1, so that jar is installed beside it.
VisibleForTesting is in both. The 13.0 jar shipped with the Kotlin
compiler does not have that annotation.

%prep
%autosetup -n java-annotations-%{version}
%setup -q -T -D -a 1 -n java-annotations-%{version}
find . -name '*.jar' -delete
find . -name '*.class' -delete

%build
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH=$JAVA_HOME/bin:$PATH
mkdir -p classes
find src/jvmMain/java -name '*.java' > sources.list
# module-info says "requires static java.desktop". jmod.deps would
# turn that into a jmod(static) provide. Without module-info the jar
# is an automatic module and requires only java.base.
javac --release 8 -encoding UTF-8 -Xlint:-options -d classes @sources.list
jar cf org.jetbrains.annotations.jar -C classes .
cat > annotations.pom <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.jetbrains</groupId>
  <artifactId>annotations</artifactId>
  <version>%{version}</version>
  <name>annotations</name>
  <description>Annotations for JVM-based languages.</description>
  <url>https://github.com/JetBrains/java-annotations</url>
  <licenses>
    <license>
      <name>Apache License, Version 2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0.txt</url>
    </license>
  </licenses>
</project>
EOF
mkdir -p classes24
find java-annotations-24.0.1/common/src/main/java java-annotations-24.0.1/java8/src/main/java \
	-name '*.java' ! -name 'module-info.java' > sources24.list
test -s sources24.list
javac --release 8 -encoding UTF-8 -Xlint:-options -d classes24 @sources24.list
jar cf org.jetbrains.annotations-24.0.1.jar -C classes24 .
cat > annotations-24.0.1.pom <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.jetbrains</groupId>
  <artifactId>annotations</artifactId>
  <version>24.0.1</version>
  <name>annotations</name>
  <description>Annotations for JVM-based languages.</description>
  <url>https://github.com/JetBrains/java-annotations</url>
  <licenses>
    <license>
      <name>Apache License, Version 2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0.txt</url>
    </license>
  </licenses>
</project>
EOF

%install
# 24.0.1 is installed first and renamed so 26.1.0 keeps annotations.sysjar.
sysjar install --buildroot %{buildroot} \
	--artifact annotations-24.0.1.pom:org.jetbrains.annotations-24.0.1.jar \
	--file-name org.jetbrains.annotations-24.0.1 \
	--filelist .mfiles24
/bin/mv %{buildroot}/usr/share/sysjar/index/org.jetbrains/annotations.sysjar \
	%{buildroot}/usr/share/sysjar/index/org.jetbrains/annotations-24.0.1.sysjar
sed -i 's|/usr/share/sysjar/index/org.jetbrains/annotations\.sysjar|/usr/share/sysjar/index/org.jetbrains/annotations-24.0.1.sysjar|' .mfiles24
sysjar install --buildroot %{buildroot} \
	--artifact annotations.pom:org.jetbrains.annotations.jar \
	--file-name org.jetbrains.annotations \
	--filelist .mfiles
while IFS= read -r line; do
	grep -qxF -- "$line" .mfiles || printf '%s\n' "$line" >> .mfiles
done < .mfiles24

%check
export JAVA_HOME=%{_jvmdir}/java-openjdk
export PATH=$JAVA_HOME/bin:$PATH
JAR=%{buildroot}%{_javadir}/org.jetbrains.annotations.jar
test -f "$JAR"
mkdir -p check
cat > check/Smoke.java <<'END'
import org.jetbrains.annotations.NotNull;
import org.jetbrains.annotations.VisibleForTesting;

public class Smoke {
	@NotNull
	@VisibleForTesting
	static final String VALUE = "ann_ok";

	public static void main(String[] args) {
		if (!"ann_ok".equals(VALUE)) {
			throw new AssertionError(VALUE);
		}
		System.out.println(VALUE);
	}
}
END
javac --release 8 -encoding UTF-8 -Xlint:-options -cp "$JAR" -d check check/Smoke.java
java -cp "check:$JAR" Smoke > check/out.log
cat check/out.log
grep -F -q ann_ok check/out.log
JAR24=%{buildroot}%{_javadir}/org.jetbrains.annotations-24.0.1.jar
test -f "$JAR24"
cat > check/Ann24.java <<'END'
import org.jetbrains.annotations.VisibleForTesting;

public class Ann24 {
	@VisibleForTesting
	static final int N = 24;

	public static void main(String[] args) {
		if (N != 24) {
			throw new AssertionError(N);
		}
		System.out.println("ann24_ok " + VisibleForTesting.class.getSimpleName());
	}
}
END
javac --release 8 -encoding UTF-8 -Xlint:-options -cp "$JAR24" -d check check/Ann24.java
java -cp "check:$JAR24" Ann24 > check/out24.log
cat check/out24.log
grep -F -q 'ann24_ok VisibleForTesting' check/out24.log
jar --describe-module -f "$JAR" > describe.txt
grep -F 'org.jetbrains.annotations automatic' describe.txt
grep -F 'requires java.base mandated' describe.txt
if grep -F 'requires static' describe.txt; then
	echo "module-info static require leaked" >&2
	exit 1
fi
jar tf "$JAR" > jar.list
grep -F 'org/jetbrains/annotations/VisibleForTesting.class' jar.list
grep -F 'org/jetbrains/annotations/NotNull.class' jar.list
if grep -F 'module-info.class' jar.list; then
	echo "module-info.class shipped" >&2
	exit 1
fi

%files -f .mfiles
%doc LICENSE.txt README.md
