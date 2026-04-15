#!/usr/bin/env python3
"""
Analyze langextract results from your enhanced API
Similar to the langextract example but using your enriched data
"""

import requests
import json
from collections import Counter
from typing import Dict, Any

def analyze_extraction_result(api_base_url: str, job_id: str):
    """
    Fetch and analyze extraction results from your enhanced langextract API
    """
    # Fetch the extraction result
    response = requests.get(f"{api_base_url}/api/v1/documents/langextract/{job_id}")
    
    if response.status_code != 200:
        print(f"Error fetching results: {response.status_code}")
        return
    
    data = response.json()
    result = data.get('result', {})
    extracted_data = result.get('extracted_data', {})
    quality_metrics = result.get('quality_metrics', {})
    
    print(f"✨ ENHANCED EXTRACTION ANALYSIS")
    print("=" * 60)
    print(f"📊 Total entities: {quality_metrics.get('total_entities', 'Unknown')}")
    print(f"🎯 Average confidence: {quality_metrics.get('average_confidence', 0)*100:.1f}%")
    print(f"📈 Entities with attributes: {quality_metrics.get('entities_with_attributes', 'Unknown')}")
    print(f"⚡ Processing time: {result.get('processing_time', 'Unknown')}s")
    print(f"🤖 Model used: {result.get('model_used', 'Unknown')}")

    # Analyze characters (if present)
    if 'characters' in extracted_data:
        characters = {}
        for entity in extracted_data['characters']:
            char_name = entity.get('text') or entity.get('value', 'Unknown')
            
            if char_name not in characters:
                characters[char_name] = {
                    "count": 0, 
                    "attributes": set(),
                    "total_confidence": 0,
                    "sources": []
                }
            
            characters[char_name]["count"] += 1
            characters[char_name]["total_confidence"] += entity.get('confidence_score', 0)
            
            # Collect attributes
            if entity.get('attributes'):
                for attr_key, attr_val in entity['attributes'].items():
                    characters[char_name]["attributes"].add(f"{attr_key}: {attr_val}")
            
            # Collect source contexts
            if entity.get('sources'):
                for source in entity['sources']:
                    characters[char_name]["sources"].append(source.get('text', ''))

        # Print character summary
        print(f"\n🎭 CHARACTER SUMMARY ({len(characters)} unique characters)")
        print("=" * 60)
        
        sorted_chars = sorted(characters.items(), key=lambda x: x[1]["count"], reverse=True)
        for char_name, char_data in sorted_chars[:10]:  # Top 10 characters
            avg_confidence = char_data["total_confidence"] / char_data["count"] if char_data["count"] > 0 else 0
            attrs_preview = list(char_data["attributes"])[:3]
            attrs_str = f" ({', '.join(attrs_preview)})" if attrs_preview else ""
            
            confidence_indicator = "🟢" if avg_confidence > 0.8 else "🟡" if avg_confidence > 0.6 else "🔴"
            
            print(f"{confidence_indicator} {char_name}: {char_data['count']} mentions "
                  f"({avg_confidence*100:.1f}% confidence){attrs_str}")

    # Entity type breakdown
    all_entities = []
    for category, entities in extracted_data.items():
        for entity in entities:
            all_entities.append({
                'category': category,
                'confidence': entity.get('confidence_score', 0),
                'has_attributes': bool(entity.get('attributes'))
            })

    if all_entities:
        entity_counts = Counter(e['category'] for e in all_entities)
        print(f"\n📊 ENTITY TYPE BREAKDOWN")
        print("=" * 60)
        
        total_entities = len(all_entities)
        for entity_type, count in entity_counts.most_common():
            percentage = (count / total_entities) * 100
            
            # Calculate average confidence for this type
            type_entities = [e for e in all_entities if e['category'] == entity_type]
            avg_confidence = sum(e['confidence'] for e in type_entities) / len(type_entities)
            entities_with_attrs = sum(1 for e in type_entities if e['has_attributes'])
            
            confidence_indicator = "🟢" if avg_confidence > 0.8 else "🟡" if avg_confidence > 0.6 else "🔴"
            
            print(f"{confidence_indicator} {entity_type}: {count} ({percentage:.1f}%) "
                  f"| Avg confidence: {avg_confidence*100:.1f}% "
                  f"| With attributes: {entities_with_attrs}/{count}")

    # Quality insights
    print(f"\n💡 QUALITY INSIGHTS")
    print("=" * 60)
    
    high_confidence_entities = [e for e in all_entities if e['confidence'] > 0.8]
    entities_with_attrs = [e for e in all_entities if e['has_attributes']]
    
    print(f"🎯 High confidence entities (>80%): {len(high_confidence_entities)}/{len(all_entities)} "
          f"({len(high_confidence_entities)/len(all_entities)*100:.1f}%)")
    print(f"📋 Entities with rich attributes: {len(entities_with_attrs)}/{len(all_entities)} "
          f"({len(entities_with_attrs)/len(all_entities)*100:.1f}%)")
    
    if result.get('extraction_config', {}).get('extraction_passes'):
        print(f"🔄 Multi-pass extraction: {result['extraction_config']['extraction_passes']} passes")
    
    print(f"🔗 Source grounding: {'Enabled' if result.get('source_grounding_enabled') else 'Disabled'}")

if __name__ == "__main__":
    # Example usage - replace with your actual API base URL and job ID
    API_BASE_URL = "http://localhost:8000"  # or your Docker container URL
    
    # You can get the job_id from the frontend or API response
    job_id = input("Enter your extraction job ID: ")
    
    analyze_extraction_result(API_BASE_URL, job_id)
