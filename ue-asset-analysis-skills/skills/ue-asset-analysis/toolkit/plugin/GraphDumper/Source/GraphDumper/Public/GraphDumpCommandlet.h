#pragma once

#include "CoreMinimal.h"
#include "Commandlets/Commandlet.h"
#include "GraphDumpCommandlet.generated.h"

/**
 * Dumps every asset under a content root to readable text:
 *   <Out>/manifest.json            asset list + package dependencies / referencers
 *   <Out>/assets/<path>.props.txt  reflected properties of every object in the package (delta vs archetype)
 *   <Out>/assets/<path>.graph.txt  readable node graphs (Blueprint / Niagara EdGraphs, Material expressions)
 *   <Out>/assets/<path>.t3d        raw copy-paste text of every EdGraph
 *   <Out>/assets/<path>.hlsl       translated material HLSL / Niagara GPU HLSL
 *
 * Usage: UnrealEditor-Cmd.exe <uproject> -run=GraphDump -Root=/Game/MyPlugin -Out=C:/Temp/Dump [-NoHLSL] [-NoMaps] [-Filter=substring]
 */
UCLASS()
class UGraphDumpCommandlet : public UCommandlet
{
	GENERATED_BODY()

public:
	UGraphDumpCommandlet();

	virtual int32 Main(const FString& Params) override;
};
