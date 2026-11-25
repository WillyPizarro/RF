import java.util.Properties

plugins {
    id("com.android.application")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

// Llave de firma del APK de release, FUERA del repositorio (CONTRATO-MIGRACION-FLUTTER §6).
// android/key.properties no se versiona (.gitignore) y apunta a un .jks fuera del repositorio:
//   storeFile=C:\ruta\fuera\del\repo\movil-buscador-release.jks
//   storePassword=…  keyAlias=…  keyPassword=…
val propiedadesFirma = Properties()
val archivoFirma = rootProject.file("key.properties")
if (archivoFirma.exists()) {
    archivoFirma.inputStream().use { propiedadesFirma.load(it) }
}

android {
    namespace = "pe.prototipo.movilbuscador"
    // 37 y no el 36 de Flutter 3.50.1: permission_handler_android 14.1.1 compila contra la API 37.
    // Solo cambia contra qué API se compila; targetSdk sigue en 36 (sin cambio de comportamiento).
    compileSdk = 37
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    defaultConfig {
        // El mismo ID de la app anterior (CONTRATO-MIGRACION-FLUTTER §6, decisión 6), para que los comandos adb run-as de HU-04 sigan valiendo.
        applicationId = "pe.prototipo.movilbuscador"
        minSdk = flutter.minSdkVersion
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    signingConfigs {
        if (archivoFirma.exists()) {
            create("release") {
                storeFile = file(propiedadesFirma.getProperty("storeFile"))
                storePassword = propiedadesFirma.getProperty("storePassword")
                keyAlias = propiedadesFirma.getProperty("keyAlias")
                keyPassword = propiedadesFirma.getProperty("keyPassword")
            }
        }
    }

    buildTypes {
        release {
            // Nunca la llave de depuración: sin key.properties, el APK de release sale sin firmar.
            signingConfig = if (archivoFirma.exists()) signingConfigs.getByName("release") else null
            isDebuggable = false
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
        }
    }
}

kotlin {
    compilerOptions {
        jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
    }
}

flutter {
    source = "../.."
}
