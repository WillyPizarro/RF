allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

val newBuildDir: Directory =
    rootProject.layout.buildDirectory
        .dir("../../build")
        .get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}
// ok_http 0.1.0 (CONTRATO-MIGRACION-FLUTTER v1.5 §6) trae jni 0.10.1, cuyos módulos de Android
// compilan contra android-31/34; sus dependencias de AndroidX piden 33 o más. Solo para esos dos
// módulos se sube compileSdk al de la app (37). No cambia minSdk ni targetSdk.
subprojects {
    if (name == "jni" || name == "ok_http") {
        afterEvaluate {
            extensions.findByName("android")?.withGroovyBuilder { "compileSdkVersion"(37) }
        }
    }
}
subprojects {
    project.evaluationDependsOn(":app")
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
