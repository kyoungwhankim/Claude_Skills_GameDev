#include "AssetRegistry/AssetRegistryModule.h"
#include "Containers/Ticker.h"
#include "HAL/IConsoleManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "Modules/ModuleManager.h"
#include "NiagaraScript.h"
#include "NiagaraSystem.h"
#include "UObject/Package.h"
#include "UObject/UObjectHash.h"

DEFINE_LOG_CATEGORY_STATIC(LogGraphDumpNiagara, Log, All);

/**
 * Niagara HLSL only exists after a compile, and the compile managers only progress inside a ticking editor.
 * Console command (run in the full editor, e.g. via -ExecCmds):
 *   GraphDump.NiagaraHLSL <Root> <OutDir> [Quit]
 * Compiles every NiagaraSystem under Root one at a time and writes <OutDir>/assets/<path>.niagara.hlsl
 */
class FGraphDumperModule : public IModuleInterface
{
	TArray<FString> Pending;
	FString OutDir;
	bool bQuitWhenDone = false;
	TWeakObjectPtr<UNiagaraSystem> Current;
	FString CurrentPkg;
	double CurrentStart = 0.0;
	int32 Done = 0;
	FTSTicker::FDelegateHandle TickHandle;
	IConsoleObject* Cmd = nullptr;

	static FString OutPathFor(const FString& Dir, FString PackageName)
	{
		PackageName.RemoveFromStart(TEXT("/Game/"));
		return FPaths::Combine(Dir, TEXT("assets"), PackageName + TEXT(".niagara.hlsl"));
	}

	void Start(const TArray<FString>& Args)
	{
		const FString Root = Args.Num() > 0 ? Args[0] : TEXT("/Game");
		OutDir = Args.Num() > 1 ? Args[1] : FPaths::Combine(FPaths::ProjectDir(), TEXT("Dump"));
		bQuitWhenDone = Args.Num() > 2 && Args[2].Equals(TEXT("Quit"), ESearchCase::IgnoreCase);

		IAssetRegistry& AR = FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get();
		AR.SearchAllAssets(true);
		TArray<FAssetData> Assets;
		AR.GetAssetsByClass(UNiagaraSystem::StaticClass()->GetClassPathName(), Assets);
		Pending.Reset();
		for (const FAssetData& A : Assets)
		{
			if (A.PackageName.ToString().StartsWith(Root)) { Pending.Add(A.PackageName.ToString()); }
		}
		Pending.Sort();
		Done = 0;
		UE_LOG(LogGraphDumpNiagara, Display, TEXT("NiagaraHLSL: %d systems under %s"), Pending.Num(), *Root);
		if (!TickHandle.IsValid())
		{
			TickHandle = FTSTicker::GetCoreTicker().AddTicker(FTickerDelegate::CreateRaw(this, &FGraphDumperModule::Tick), 0.1f);
		}
	}

	void WriteCurrent(bool bTimedOut)
	{
		UNiagaraSystem* Sys = Current.Get();
		if (!Sys) { return; }
		TArray<UObject*> Objects;
		GetObjectsWithPackage(Sys->GetPackage(), Objects, true);
		FString Out;
		if (bTimedOut) { Out += TEXT("// WARNING: compile timed out, output may be incomplete\n"); }
		for (UObject* Obj : Objects)
		{
			UNiagaraScript* S = Cast<UNiagaraScript>(Obj);
			if (!S) { continue; }
			const FNiagaraVMExecutableData& VM = S->GetVMExecutableData();
			if (!VM.LastHlslTranslation.IsEmpty())
			{
				Out += FString::Printf(TEXT("\n// ================ CPU/VM %s\n%s\n"), *S->GetPathName(), *VM.LastHlslTranslation);
			}
			if (!VM.LastHlslTranslationGPU.IsEmpty())
			{
				Out += FString::Printf(TEXT("\n// ================ GPU %s\n%s\n"), *S->GetPathName(), *VM.LastHlslTranslationGPU);
			}
		}
		FFileHelper::SaveStringToFile(Out, *OutPathFor(OutDir, CurrentPkg), FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
		++Done;
		UE_LOG(LogGraphDumpNiagara, Display, TEXT("NiagaraHLSL: [%d] %s (%d chars)%s"), Done, *CurrentPkg, Out.Len(), bTimedOut ? TEXT(" TIMEOUT") : TEXT(""));
	}

	bool Tick(float)
	{
		if (UNiagaraSystem* Sys = Current.Get())
		{
			const bool bTimedOut = FPlatformTime::Seconds() - CurrentStart > 180.0;
			// The editor's compiling manager consumes the completion itself, so poll for "nothing outstanding" instead.
			const bool bBusy = Sys->NeedsRequestCompile() || Sys->HasOutstandingCompilationRequests(false);
			if (bBusy && !bTimedOut)
			{
				return true;
			}
			WriteCurrent(bTimedOut);
			Current.Reset();
			CollectGarbage(GARBAGE_COLLECTION_KEEPFLAGS);
		}

		while (Pending.Num() > 0)
		{
			CurrentPkg = Pending[0];
			Pending.RemoveAt(0);
			UPackage* Pkg = LoadPackage(nullptr, *CurrentPkg, LOAD_NoWarn);
			UNiagaraSystem* Sys = Pkg ? FindObject<UNiagaraSystem>(Pkg, *FPackageName::GetShortName(CurrentPkg)) : nullptr;
			if (!Sys)
			{
				UE_LOG(LogGraphDumpNiagara, Warning, TEXT("NiagaraHLSL: failed to load %s"), *CurrentPkg);
				continue;
			}
			Sys->RequestCompile(true);
			Current = Sys;
			CurrentStart = FPlatformTime::Seconds();
			return true;
		}

		UE_LOG(LogGraphDumpNiagara, Display, TEXT("NiagaraHLSL finished: %d systems"), Done);
		TickHandle.Reset();
		if (bQuitWhenDone)
		{
			FPlatformMisc::RequestExit(false, TEXT("GraphDump.NiagaraHLSL"));
		}
		return false;
	}

public:
	virtual void StartupModule() override
	{
		Cmd = IConsoleManager::Get().RegisterConsoleCommand(TEXT("GraphDump.NiagaraHLSL"),
			TEXT("GraphDump.NiagaraHLSL <Root> <OutDir> [Quit] - compile Niagara systems and dump generated HLSL"),
			FConsoleCommandWithArgsDelegate::CreateRaw(this, &FGraphDumperModule::Start));
	}

	virtual void ShutdownModule() override
	{
		if (Cmd) { IConsoleManager::Get().UnregisterConsoleObject(Cmd); }
		if (TickHandle.IsValid()) { FTSTicker::GetCoreTicker().RemoveTicker(TickHandle); }
	}
};

IMPLEMENT_MODULE(FGraphDumperModule, GraphDumper);
