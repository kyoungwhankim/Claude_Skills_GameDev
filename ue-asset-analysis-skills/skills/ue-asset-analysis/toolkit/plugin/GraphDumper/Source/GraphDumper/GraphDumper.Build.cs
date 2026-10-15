using UnrealBuildTool;

public class GraphDumper : ModuleRules
{
	public GraphDumper(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
		CppStandard = CppStandardVersion.Cpp20;
		PublicDependencyModuleNames.AddRange(new string[] { "Core", "CoreUObject", "Engine" });
		PrivateDependencyModuleNames.AddRange(new string[]
		{
			"UnrealEd", "AssetRegistry", "BlueprintGraph", "Kismet", "Json", "JsonUtilities",
			"RenderCore", "RHI", "Niagara", "NiagaraCore", "NiagaraEditor", "MaterialEditor"
		});
	}
}
