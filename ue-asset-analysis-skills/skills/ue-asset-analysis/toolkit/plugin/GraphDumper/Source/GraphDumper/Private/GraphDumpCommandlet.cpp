#include "GraphDumpCommandlet.h"

#include "AssetRegistry/AssetRegistryModule.h"
#include "AssetRegistry/IAssetRegistry.h"
#include "EdGraph/EdGraph.h"
#include "EdGraph/EdGraphNode.h"
#include "EdGraph/EdGraphPin.h"
#include "EdGraphUtilities.h"
#include "Engine/Blueprint.h"
#include "Engine/World.h"
#include "HAL/FileManager.h"
#include "MaterialShared.h"
#include "Materials/Material.h"
#include "Materials/MaterialExpression.h"
#include "Materials/MaterialFunction.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "NiagaraScript.h"
#include "Policies/PrettyJsonPrintPolicy.h"
#include "RHIGlobals.h"
#include "Serialization/JsonWriter.h"
#include "UObject/Package.h"
#include "UObject/UObjectHash.h"
#include "UObject/UnrealType.h"

DEFINE_LOG_CATEGORY_STATIC(LogGraphDump, Log, All);

namespace GraphDump
{
	/** FMaterialResource::SetMaterial takes an ERHIFeatureLevel up to UE 5.5 and an EShaderPlatform from 5.7; pick whichever compiles. */
	template <typename TResource>
	static void InitMaterialResource(TResource* Res, UMaterial* M)
	{
		if constexpr (requires { Res->SetMaterial(M, (UMaterialInstance*)nullptr, SP_PCD3D_SM5, EMaterialQualityLevel::High); })
		{
			Res->SetMaterial(M, nullptr, SP_PCD3D_SM5, EMaterialQualityLevel::High);
		}
		else
		{
			Res->SetMaterial(M, nullptr, ERHIFeatureLevel::SM5, EMaterialQualityLevel::High);
		}
	}

	/**
	 * Some engine calls (e.g. UMaterialExpression::GetCaption on a malformed expression) dereference null and would
	 * kill the whole commandlet. Run each object/expression dump through SEH so one bad asset only costs its own output.
	 */
#if PLATFORM_WINDOWS
	static bool SehInvoke(void (*Fn)(void*), void* Ctx)
	{
		__try
		{
			Fn(Ctx);
			return true;
		}
		__except (1 /* EXCEPTION_EXECUTE_HANDLER */)
		{
			return false;
		}
	}
#else
	static bool SehInvoke(void (*Fn)(void*), void* Ctx)
	{
		Fn(Ctx);
		return true;
	}
#endif

	template <typename F>
	static bool Guarded(F& Fn)
	{
		return SehInvoke([](void* P) { (*static_cast<F*>(P))(); }, &Fn);
	}

	static TArray<FString> Errors;

	static constexpr int32 MaxValueLen = 16000;

	static FString OneLine(FString S)
	{
		S.ReplaceInline(TEXT("\r"), TEXT(""));
		S.ReplaceInline(TEXT("\n"), TEXT(" | "));
		return S;
	}

	static FString Clip(const FString& S)
	{
		return S.Len() > MaxValueLen ? S.Left(MaxValueLen) + FString::Printf(TEXT(" ...<clipped %d chars>"), S.Len() - MaxValueLen) : S;
	}

	static bool IsExpressionInputStruct(const FProperty* P)
	{
		if (const FStructProperty* SP = CastField<FStructProperty>(P))
		{
			const FString N = SP->Struct->GetName();
			return N.Contains(TEXT("ExpressionInput")) || N.Contains(TEXT("MaterialInput")) || N.Contains(TEXT("MaterialAttributesInput"));
		}
		return false;
	}

	/** Properties of Obj that differ from its archetype, as "Name = ExportText" lines. */
	static void AppendProps(UObject* Obj, FString& Out, const TCHAR* Indent, const TSet<FName>* Skip = nullptr, bool bSkipExprInputs = false)
	{
		UObject* Arch = Obj->GetArchetype();
		for (TFieldIterator<FProperty> It(Obj->GetClass()); It; ++It)
		{
			FProperty* P = *It;
			if (P->HasAnyPropertyFlags(CPF_Transient | CPF_DuplicateTransient | CPF_Deprecated))
			{
				continue;
			}
			if (Skip && Skip->Contains(P->GetFName()))
			{
				continue;
			}
			if (bSkipExprInputs && IsExpressionInputStruct(P))
			{
				continue;
			}
			const UClass* Owner = P->GetOwnerClass();
			const void* Def = (Arch && Owner && Arch->GetClass()->IsChildOf(Owner)) ? (const void*)Arch : nullptr;
			for (int32 i = 0; i < P->ArrayDim; ++i)
			{
				if (Def && P->Identical_InContainer(Obj, Def, i, PPF_None))
				{
					continue;
				}
				FString V;
				P->ExportText_InContainer(i, V, Obj, Def, Obj, PPF_None);
				// Long arrays (e.g. Blueprint NewVariables) would be clipped as one line, so emit one element per line.
				const FArrayProperty* AP = CastField<FArrayProperty>(P);
				if (AP && V.Len() > 4000)
				{
					FScriptArrayHelper Helper(AP, AP->ContainerPtrToValuePtr<void>(Obj, i));
					Out += FString::Printf(TEXT("%s%s = <%d elements>\n"), Indent, *P->GetName(), Helper.Num());
					for (int32 e = 0; e < Helper.Num(); ++e)
					{
						FString EV;
						AP->Inner->ExportTextItem_Direct(EV, Helper.GetRawPtr(e), nullptr, Obj, PPF_None);
						Out += FString::Printf(TEXT("%s%s[%d] = %s\n"), Indent, *P->GetName(), e, *Clip(OneLine(EV)));
					}
					continue;
				}
				if (P->ArrayDim > 1)
				{
					Out += FString::Printf(TEXT("%s%s[%d] = %s\n"), Indent, *P->GetName(), i, *Clip(OneLine(V)));
				}
				else
				{
					Out += FString::Printf(TEXT("%s%s = %s\n"), Indent, *P->GetName(), *Clip(OneLine(V)));
				}
			}
		}
	}

	static FString PinTypeString(const FEdGraphPinType& T)
	{
		FString S = T.PinCategory.ToString();
		if (T.PinSubCategoryObject.IsValid())
		{
			S += TEXT(":") + T.PinSubCategoryObject->GetName();
		}
		else if (!T.PinSubCategory.IsNone())
		{
			S += TEXT(":") + T.PinSubCategory.ToString();
		}
		if (T.IsArray()) { S = TEXT("Array<") + S + TEXT(">"); }
		else if (T.IsSet()) { S = TEXT("Set<") + S + TEXT(">"); }
		else if (T.IsMap()) { S = TEXT("Map<") + S + TEXT(",") + T.PinValueType.TerminalCategory.ToString() + TEXT(">"); }
		if (T.bIsReference) { S += TEXT("&"); }
		return S;
	}

	static void DumpEdGraph(UEdGraph* G, FString& Out, FString& T3D)
	{
		Out += FString::Printf(TEXT("\n################ GRAPH %s\n# class=%s schema=%s nodes=%d\n"),
			*G->GetPathName(), *G->GetClass()->GetName(), G->Schema ? *G->Schema->GetName() : TEXT("-"), G->Nodes.Num());

		TMap<const UEdGraphNode*, int32> Ids;
		for (int32 i = 0; i < G->Nodes.Num(); ++i)
		{
			if (G->Nodes[i]) { Ids.Add(G->Nodes[i], i); }
		}

		TSet<UObject*> ToExport;
		for (int32 i = 0; i < G->Nodes.Num(); ++i)
		{
			UEdGraphNode* N = G->Nodes[i];
			if (!N) { continue; }
			ToExport.Add(N);

			const FString Title = OneLine(N->GetNodeTitle(ENodeTitleType::FullTitle).ToString());
			Out += FString::Printf(TEXT("\n[N%d] %s \"%s\" @(%d,%d)%s\n"), i, *N->GetClass()->GetName(), *Title,
				N->NodePosX, N->NodePosY, N->IsNodeEnabled() ? TEXT("") : TEXT(" DISABLED"));
			if (!N->NodeComment.IsEmpty())
			{
				Out += FString::Printf(TEXT("    // %s\n"), *OneLine(N->NodeComment));
			}
			for (UEdGraphPin* Pin : N->Pins)
			{
				if (!Pin) { continue; }
				const bool bLinked = Pin->LinkedTo.Num() > 0;
				FString Def = Pin->DefaultObject ? Pin->DefaultObject->GetPathName()
					: (!Pin->DefaultTextValue.IsEmpty() ? Pin->DefaultTextValue.ToString() : Pin->DefaultValue);
				if (Pin->bHidden && !bLinked && Def.IsEmpty()) { continue; }

				FString Line = FString::Printf(TEXT("    %s %s (%s)"), Pin->Direction == EGPD_Input ? TEXT("in ") : TEXT("out"),
					*Pin->PinName.ToString(), *PinTypeString(Pin->PinType));
				if (!bLinked && !Def.IsEmpty())
				{
					Line += TEXT(" = ") + Clip(OneLine(Def));
				}
				for (UEdGraphPin* L : Pin->LinkedTo)
				{
					if (!L) { continue; }
					const UEdGraphNode* LN = L->GetOwningNodeUnchecked();
					const int32* Id = LN ? Ids.Find(LN) : nullptr;
					Line += FString::Printf(TEXT(" %s N%s.%s"), Pin->Direction == EGPD_Input ? TEXT("<-") : TEXT("->"),
						Id ? *FString::FromInt(*Id) : TEXT("?"), *L->PinName.ToString());
				}
				if (Pin->bHidden) { Line += TEXT(" [hidden]"); }
				Out += Line + TEXT("\n");
			}
		}

		FString Text;
		FEdGraphUtilities::ExportNodesToText(ToExport, Text);
		T3D += FString::Printf(TEXT("\n// ================ GRAPH %s\n"), *G->GetPathName());
		T3D += Text;
	}

	static void DumpMaterialExpressions(UObject* Owner, TConstArrayView<TObjectPtr<UMaterialExpression>> Exprs, UMaterial* Mat, FString& Out)
	{
		Out += FString::Printf(TEXT("\n################ MATERIAL GRAPH %s\n# expressions=%d\n"), *Owner->GetPathName(), Exprs.Num());

		TMap<const UMaterialExpression*, int32> Ids;
		for (int32 i = 0; i < Exprs.Num(); ++i)
		{
			if (Exprs[i]) { Ids.Add(Exprs[i], i); }
		}

		static const TSet<FName> Skip = {
			TEXT("Material"), TEXT("Function"), TEXT("MaterialExpressionEditorX"), TEXT("MaterialExpressionEditorY"),
			TEXT("MaterialExpressionGuid"), TEXT("GraphNode"), TEXT("Outputs"), TEXT("bRealtimePreview"),
			TEXT("bNeedToUpdatePreview"), TEXT("bCollapsed"), TEXT("bShowOutputNameOnPin"), TEXT("ExpressionGUID"),
		};

		auto LinkStr = [&Ids](const FExpressionInput* In) -> FString
		{
			if (!In || !In->Expression) { return FString(); }
			const int32* Id = Ids.Find(In->Expression);
			FString OutName;
			TArray<FExpressionOutput>& Outs = In->Expression->GetOutputs();
			if (Outs.IsValidIndex(In->OutputIndex) && !Outs[In->OutputIndex].OutputName.IsNone())
			{
				OutName = Outs[In->OutputIndex].OutputName.ToString();
			}
			else
			{
				OutName = FString::Printf(TEXT("out%d"), In->OutputIndex);
			}
			FString S = FString::Printf(TEXT("<- E%s.%s"), Id ? *FString::FromInt(*Id) : TEXT("?"), *OutName);
			if (In->Mask)
			{
				S += FString::Printf(TEXT(" mask(%s%s%s%s)"), In->MaskR ? TEXT("R") : TEXT(""), In->MaskG ? TEXT("G") : TEXT(""),
					In->MaskB ? TEXT("B") : TEXT(""), In->MaskA ? TEXT("A") : TEXT(""));
			}
			return S;
		};

		for (int32 i = 0; i < Exprs.Num(); ++i)
		{
			UMaterialExpression* E = Exprs[i];
			if (!E) { continue; }
			auto DumpOne = [&]()
			{
				TArray<FString> Captions;
				E->GetCaption(Captions);
				Out += FString::Printf(TEXT("\n[E%d] %s \"%s\" @(%d,%d)\n"), i, *E->GetClass()->GetName(),
					*OneLine(FString::Join(Captions, TEXT(" / "))), E->MaterialExpressionEditorX, E->MaterialExpressionEditorY);
				if (!E->Desc.IsEmpty())
				{
					Out += FString::Printf(TEXT("    // %s\n"), *OneLine(E->Desc));
				}
				TArrayView<FExpressionInput*> Inputs = E->GetInputsView();
				for (int32 k = 0; k < Inputs.Num(); ++k)
				{
					FExpressionInput* In = Inputs[k];
					FString L = LinkStr(In);
					if (!L.IsEmpty())
					{
						Out += FString::Printf(TEXT("    in  %s %s\n"), *E->GetInputName(k).ToString(), *L);
					}
				}
				FString Props;
				AppendProps(E, Props, TEXT("    . "), &Skip, true);
				Out += Props;
			};
			if (!Guarded(DumpOne))
			{
				Out += FString::Printf(TEXT("\n[E%d] %s <dump failed: engine exception>\n"), i, *E->GetClass()->GetName());
				Errors.Add(FString::Printf(TEXT("%s  E%d %s"), *Owner->GetPathName(), i, *E->GetClass()->GetName()));
			}
		}

		if (Mat)
		{
			Out += TEXT("\n[MATERIAL OUTPUTS]\n");
			const UEnum* Enum = StaticEnum<EMaterialProperty>();
			for (int32 p = 0; p < (int32)MP_MAX; ++p)
			{
				FExpressionInput* In = Mat->GetExpressionInputForProperty((EMaterialProperty)p);
				FString L = LinkStr(In);
				if (!L.IsEmpty())
				{
					Out += FString::Printf(TEXT("    %s %s\n"), Enum ? *Enum->GetNameStringByValue(p) : *FString::FromInt(p), *L);
				}
			}
		}
	}

	static FString OutPathFor(const FString& OutDir, const FString& PackageName, const TCHAR* Ext)
	{
		FString Rel = PackageName;
		Rel.RemoveFromStart(TEXT("/Game/"));
		Rel.RemoveFromStart(TEXT("/"));
		return FPaths::Combine(OutDir, TEXT("assets"), Rel + Ext);
	}
}

UGraphDumpCommandlet::UGraphDumpCommandlet()
{
	IsClient = false;
	IsServer = false;
	IsEditor = true;
	LogToConsole = true;
}

int32 UGraphDumpCommandlet::Main(const FString& Params)
{
	using namespace GraphDump;

	FString Root = TEXT("/Game");
	FString OutDir = FPaths::Combine(FPaths::ProjectDir(), TEXT("Dump"));
	FString Filter;
	FParse::Value(*Params, TEXT("Root="), Root);
	FParse::Value(*Params, TEXT("Out="), OutDir);
	FParse::Value(*Params, TEXT("Filter="), Filter);
	const bool bNoHLSL = FParse::Param(*Params, TEXT("NoHLSL"));
	const bool bNoMaps = FParse::Param(*Params, TEXT("NoMaps"));
	OutDir = FPaths::ConvertRelativePathToFull(OutDir);

	IAssetRegistry& AR = FModuleManager::LoadModuleChecked<FAssetRegistryModule>(TEXT("AssetRegistry")).Get();
	AR.SearchAllAssets(true);

	TArray<FAssetData> Assets;
	AR.GetAssetsByPath(FName(*Root), Assets, true);
	Assets.Sort([](const FAssetData& A, const FAssetData& B)
	{
		// Maps last so heavy worlds load after everything else has been dumped.
		const bool AM = A.AssetClassPath.GetAssetName() == TEXT("World");
		const bool BM = B.AssetClassPath.GetAssetName() == TEXT("World");
		if (AM != BM) { return BM; }
		return A.PackageName.LexicalLess(B.PackageName);
	});

	UE_LOG(LogGraphDump, Display, TEXT("GraphDump: %d assets under %s -> %s"), Assets.Num(), *Root, *OutDir);

	// ---- manifest
	{
		FString Json;
		TSharedRef<TJsonWriter<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>> W = TJsonWriterFactory<TCHAR, TPrettyJsonPrintPolicy<TCHAR>>::Create(&Json);
		W->WriteArrayStart();
		for (const FAssetData& A : Assets)
		{
			W->WriteObjectStart();
			W->WriteValue(TEXT("package"), A.PackageName.ToString());
			W->WriteValue(TEXT("asset"), A.AssetName.ToString());
			W->WriteValue(TEXT("class"), A.AssetClassPath.ToString());

			TArray<FName> Deps, Refs;
			AR.GetDependencies(A.PackageName, Deps, UE::AssetRegistry::EDependencyCategory::Package);
			AR.GetReferencers(A.PackageName, Refs, UE::AssetRegistry::EDependencyCategory::Package);
			W->WriteArrayStart(TEXT("dependencies"));
			for (const FName& D : Deps) { if (!D.ToString().StartsWith(TEXT("/Script/"))) { W->WriteValue(D.ToString()); } }
			W->WriteArrayEnd();
			W->WriteArrayStart(TEXT("referencers"));
			for (const FName& R : Refs) { W->WriteValue(R.ToString()); }
			W->WriteArrayEnd();

			W->WriteObjectStart(TEXT("tags"));
			A.EnumerateTags([&W](const TPair<FName, FAssetTagValueRef>& Tag)
			{
				FString V = Tag.Value.AsString();
				if (V.Len() < 2000) { W->WriteValue(Tag.Key.ToString(), V); }
			});
			W->WriteObjectEnd();
			W->WriteObjectEnd();
		}
		W->WriteArrayEnd();
		W->Close();
		FFileHelper::SaveStringToFile(Json, *FPaths::Combine(OutDir, TEXT("manifest.json")), FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
	}

	TSet<FName> Done;
	int32 Count = 0, Failed = 0;
	for (const FAssetData& A : Assets)
	{
		if (Done.Contains(A.PackageName)) { continue; }
		Done.Add(A.PackageName);

		const FString PkgName = A.PackageName.ToString();
		if (!Filter.IsEmpty() && !PkgName.Contains(Filter)) { continue; }
		const bool bIsMap = A.AssetClassPath.GetAssetName() == TEXT("World");
		if (bIsMap && bNoMaps) { continue; }

		UPackage* Pkg = LoadPackage(nullptr, *PkgName, LOAD_NoWarn);
		if (!Pkg)
		{
			UE_LOG(LogGraphDump, Warning, TEXT("Failed to load %s"), *PkgName);
			++Failed;
			continue;
		}

		TArray<UObject*> Objects;
		GetObjectsWithPackage(Pkg, Objects, true);

		FString Props, Graph, T3D, Hlsl;
		Props += FString::Printf(TEXT("# PACKAGE %s\n# primary class: %s\n"), *PkgName, *A.AssetClassPath.ToString());

		for (UObject* Obj : Objects)
		{
			if (!Obj || Obj->IsA<UEdGraphNode>() || Obj->IsA<UMaterialExpression>()) { continue; }

			auto DumpObject = [&]()
			{
				if (UEdGraph* G = Cast<UEdGraph>(Obj))
				{
					DumpEdGraph(G, Graph, T3D);
					return;
				}

				Props += FString::Printf(TEXT("\n=== %s (%s)\n"), *Obj->GetPathName(Pkg), *Obj->GetClass()->GetPathName());
				if (UBlueprint* BP = Cast<UBlueprint>(Obj))
				{
					Props += FString::Printf(TEXT("  #ParentClass = %s\n  #GeneratedClass = %s\n"),
						BP->ParentClass ? *BP->ParentClass->GetPathName() : TEXT("-"),
						BP->GeneratedClass ? *BP->GeneratedClass->GetPathName() : TEXT("-"));
				}
				AppendProps(Obj, Props, TEXT("  "), nullptr, Obj->IsA<UMaterial>());

				if (UMaterial* M = Cast<UMaterial>(Obj))
				{
					DumpMaterialExpressions(M, M->GetExpressions(), M, Graph);
					if (!bNoHLSL)
					{
						// Commandlets don't cache render resources, so translate through a temporary resource.
						TUniquePtr<FMaterialResource> TempRes(M->AllocateResource());
						InitMaterialResource(TempRes.Get(), M);
						if (FMaterialResource* Res = TempRes.Get())
						{
							FString Src;
							if (Res->GetMaterialExpressionSource(Src))
							{
								Hlsl += FString::Printf(TEXT("// ================ MATERIAL %s (SM5)\n"), *M->GetPathName());
								Hlsl += Src + TEXT("\n");
							}
						}
					}
				}
				else if (UMaterialFunction* MF = Cast<UMaterialFunction>(Obj))
				{
					DumpMaterialExpressions(MF, MF->GetExpressions(), nullptr, Graph);
				}
				else if (UNiagaraScript* NS = Cast<UNiagaraScript>(Obj))
				{
					const FNiagaraVMExecutableData& VM = NS->GetVMExecutableData();
					if (!VM.LastHlslTranslationGPU.IsEmpty())
					{
						Hlsl += FString::Printf(TEXT("// ================ NIAGARA GPU %s\n%s\n"), *NS->GetPathName(), *VM.LastHlslTranslationGPU);
					}
					if (!VM.LastHlslTranslation.IsEmpty())
					{
						Hlsl += FString::Printf(TEXT("// ================ NIAGARA CPU %s\n%s\n"), *NS->GetPathName(), *VM.LastHlslTranslation);
					}
				}
			};
			if (!Guarded(DumpObject))
			{
				Props += FString::Printf(TEXT("\n=== %s <dump failed: engine exception>\n"), *Obj->GetPathName(Pkg));
				Errors.Add(Obj->GetPathName());
				UE_LOG(LogGraphDump, Warning, TEXT("Dump failed (engine exception): %s"), *Obj->GetPathName());
			}
		}

		const auto Save = [](const FString& S, const FString& Path)
		{
			FFileHelper::SaveStringToFile(S, *Path, FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
		};
		Save(Props, OutPathFor(OutDir, PkgName, TEXT(".props.txt")));
		if (!Graph.IsEmpty()) { Save(Graph, OutPathFor(OutDir, PkgName, TEXT(".graph.txt"))); }
		if (!T3D.IsEmpty()) { Save(T3D, OutPathFor(OutDir, PkgName, TEXT(".t3d"))); }
		if (!Hlsl.IsEmpty()) { Save(Hlsl, OutPathFor(OutDir, PkgName, TEXT(".hlsl"))); }

		++Count;
		if (Count % 50 == 0)
		{
			UE_LOG(LogGraphDump, Display, TEXT("GraphDump: %d packages done"), Count);
			CollectGarbage(GARBAGE_COLLECTION_KEEPFLAGS);
		}
		if (bIsMap)
		{
			CollectGarbage(GARBAGE_COLLECTION_KEEPFLAGS);
		}
	}

	FFileHelper::SaveStringToFile(FString::Join(Errors, TEXT("\n")), *FPaths::Combine(OutDir, TEXT("dump_errors.txt")), FFileHelper::EEncodingOptions::ForceUTF8WithoutBOM);
	UE_LOG(LogGraphDump, Display, TEXT("GraphDump finished: %d packages dumped, %d failed, %d object errors (see dump_errors.txt)"), Count, Failed, Errors.Num());
	return 0;
}
