Name:		jetbrains-annotations
Version:	26.1.0
Release:	1
Summary:	Nullability and API-contract annotations
Group:		Development/Java
License:	Apache-2.0
URL:		https://github.com/JetBrains/java-annotations
# The git tag ships gradle/wrapper/gradle-wrapper.jar. That prebuilt
# wrapper is removed from this archive, and %prep deletes it if it
# comes back. commonMain is Kotlin and is not compiled.
Source0:	https://github.com/JetBrains/java-annotations/archive/refs/tags/%{version}.tar.gz#/jetbrains-annotations-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-current-devel
BuildRequires:	sysjar

%description
JetBrains annotations document nullability and API contracts for JVM
languages. Gradle 8.11.1 pins org.jetbrains:annotations 24.0.1, and
its build logic imports VisibleForTesting. That annotation is absent
from the 13.0 jar shipped with the Kotlin compiler. 26.1.0 is the
current release and stays compatible with the 24.0.1 API.

%prep
%autosetup -n java-annotations-%{version}
rm -f gradle/wrapper/gradle-wrapper.jar

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

%install
sysjar install --buildroot %{buildroot} \
	--artifact annotations.pom:org.jetbrains.annotations.jar \
	--file-name org.jetbrains.annotations \
	--filelist .mfiles

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
test "$(java -cp "check:$JAR" Smoke)" = ann_ok
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
