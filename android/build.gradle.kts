buildscript {
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath("com.google.gms:google-services:4.4.4")
        classpath("org.jetbrains.kotlin:kotlin-gradle-plugin:2.1.0")
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
        maven { url = uri("https://jitpack.io") }
    }
    
    configurations.all {
        resolutionStrategy.eachDependency {
            if (requested.group == "androidx.core" && requested.name.startsWith("core")) {
                useVersion("1.13.1")
            }
            if (requested.group == "androidx.browser" && requested.name == "browser") {
                useVersion("1.8.0")
            }
            if (requested.group == "androidx.lifecycle" && requested.name.startsWith("lifecycle")) {
                useVersion("2.8.2")
            }
        }
    }
}

subprojects {
    afterEvaluate {
        if (hasProperty("android")) {
            val android = extensions.getByName("android") as com.android.build.gradle.BaseExtension
            
            if (project.name == "installed_apps") {
                android.compileSdkVersion(34)
            } else {
                android.compileSdkVersion(35)
            }
            
            android.compileOptions {
                sourceCompatibility = JavaVersion.VERSION_17
                targetCompatibility = JavaVersion.VERSION_17
            }
        }
    }

    tasks.withType<org.jetbrains.kotlin.gradle.tasks.KotlinCompilationTask<*>>().configureEach {
        compilerOptions {
            if (this is org.jetbrains.kotlin.gradle.dsl.KotlinJvmCompilerOptions) {
                jvmTarget.set(org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17)
            }
            freeCompilerArgs.addAll(
                "-Xskip-prerelease-check", 
                "-Xno-param-assertion",
                "-Xjvm-default=all",
                "-Xno-call-assertions",
                "-Xno-receiver-assertions",
                "-Xsuppress-version-warnings"
            )
        }
    }
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
