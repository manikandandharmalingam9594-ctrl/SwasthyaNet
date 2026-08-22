import React, { useState, useEffect, useRef } from 'react';
import { 
  Mic, 
  MicOff, 
  Volume2, 
  CheckCircle2, 
  AlertTriangle, 
  X, 
  Languages, 
  Loader2, 
  ArrowRight, 
  Sparkles,
  HelpCircle,
  RotateCcw
} from 'lucide-react';
import api from '../services/api';

// Number words dictionaries
const NUMBER_WORDS = {
  // English
  'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5, 'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
  'eleven': 11, 'twelve': 12, 'thirteen': 13, 'fourteen': 14, 'fifteen': 15, 'sixteen': 16, 'seventeen': 17,
  'eighteen': 18, 'nineteen': 19, 'twenty': 20, 'twenty-five': 25, 'thirty': 30, 'forty': 40, 'fifty': 50,
  'sixty': 60, 'seventy': 70, 'eighty': 80, 'ninety': 90, 'hundred': 100,
  // Hindi
  'एक': 1, 'दो': 2, 'तीन': 3, 'चार': 4, 'पांच': 5, 'पाँच': 5, 'छह': 6, 'छः': 6, 'सात': 7, 'आठ': 8, 'नौ': 9, 'दस': 10,
  'ग्यारह': 11, 'बारह': 12, 'तेरह': 13, 'चौदह': 14, 'पंद्रह': 15, 'सोलह': 16, 'सत्रह': 17, 'अठारह': 18, 'उन्नीस': 19, 'बीस': 20,
  'पच्चीस': 25, 'तीस': 30, 'पैंतीस': 35, 'चालीस': 40, 'पचास': 50, 'सौ': 100,
  // Tamil
  'ஒன்று': 1, 'இரண்டு': 2, 'மூன்று': 3, 'நான்கு': 4, 'ஐந்து': 5, 'ஆறு': 6, 'ஏழு': 7, 'எட்டு': 8, 'ஒன்பது': 9, 'பத்து': 10,
  'பதினொன்று': 11, 'பன்னிரண்டு': 12, 'பதின்மூன்று': 13, 'பதினான்கு': 14, 'பதினைந்து': 15, 'பதினாறு': 16,
  'பதினேழு': 17, 'பதினெட்டு': 18, 'பத்தொன்பது': 19, 'இருபது': 20, 'இருபத்தைந்து': 25, 'முப்பது': 30, 'நாற்பது': 40, 'ஐம்பது': 50, 'நூறு': 100
};

// Multilingual Medicine Aliases
const MEDICINE_ALIASES = {
  1: ['paracetamol', 'crocin', 'calpol', 'dolo', 'पैरासिटामोल', 'पॅरासिटामोल', 'பாராசிட்டமால்', 'பாராசிட்டமோல்'],
  2: ['ibuprofen', 'brufen', 'आइबूप्रोफेन', 'इबुप्रोफेन', 'இபுப்ரோஃபென்', 'ஐபுப்ரோஃபென்'],
  3: ['amoxicillin', 'mox', 'novamox', 'अमोक्सिसिलिन', 'अमोक्सीसिलीन', 'அமோக்சிசிலின்', 'அமாக்சிசிலின்'],
  4: ['azithromycin', 'zithromax', 'azithral', 'एज़िथ्रोमाइसिन', 'अज़ीथ्रोमाइसिन', 'அசித்ரோமைசின்'],
  5: ['ciprofloxacin', 'ciptox', 'सिप्रोफ्लोक्सासिन', 'சிப்ரோஃப்ளோக்சசின்'],
  6: ['metronidazole', 'flagyl', 'मेट्रोनिडाजोल', 'மெட்ரானிடசோல்'],
  7: ['cetirizine', 'cetzine', 'सेटीरिज़िन', 'சிட்ரிசின்'],
  8: ['omeprazole', 'omez', 'ओमेप्राजोल', 'ஒமேப்ராசோல்'],
  9: ['pantoprazole', 'pantocid', 'पेन्टोप्राजोल', 'பான்டோப்ராசோல்'],
  10: ['ors', 'oral rehydration', 'ओआरएस', 'ஓஆர்எஸ்', 'ஓ ஆர் எஸ்'],
  11: ['zinc', 'zinc tablets', 'जिंक', 'துத்தநாகம்', 'ஜிங்க்'],
  12: ['iron', 'folic acid', 'ifa', 'आयरन', 'இரும்பு சத்து'],
  13: ['calcium', 'calcium tablets', 'कैल्शियम', 'கால்சியம்'],
  14: ['amlodipine', 'एम्लोडिपिन', 'ஆம்லோடிபைன்'],
  15: ['losartan', 'लोसार्टन', 'லோசார்டன்'],
  16: ['metformin', 'glycomet', 'मेटफॉर्मिन', 'மெட்பார்மின்'],
  17: ['salbutamol', 'asthalin', 'सालबुटामोल', 'சல்பூட்டமால்'],
  18: ['hydrocortisone', 'हाइड्रोकार्टिसोन', 'ஹைட்ரோகார்ட்டிசோன்'],
  19: ['normal saline', 'saline', 'नॉर्मल सलाइन', 'சலைன்'],
  20: ['povidone iodine', 'povidone', 'betadine', 'iodine', 'पोविडोन', 'பொவிடோன்']
};

// Action Keywords
const ACTION_KEYWORDS = {
  IN: [
    'add', 'added', 'received', 'incoming', 'plus', 'stock in', 'receive', 'got', 'enter', 'stock is', 'put', 'in',
    'जोड़ें', 'जोड़े', 'जोड़ो', 'मिलाएं', 'आया', 'प्राप्त', 'प्राप्त हुआ', 'डालें', 'डालो', 'इन', 'jodo', 'aaya', 'prapt',
    'சேர்க்கவும்', 'சேர்', 'சேர்க்க', 'வந்தது', 'வரவு', 'கூட்டு', 'உள்ளே', 'serkkavum', 'ser', 'vandhadhu'
  ],
  OUT: [
    'remove', 'dispense', 'dispensed', 'use', 'used', 'reduce', 'minus', 'outgoing', 'subtract', 'gave', 'taken', 'prescribed', 'out',
    'निकालें', 'निकाले', 'निकालो', 'घटाएं', 'कम करें', 'दिया', 'उपयोग', 'उपयोग किया', 'खर्च', 'आउट', 'nikalo', 'kam karo', 'diya',
    'குறைக்கவும்', 'குறைக்க', 'எடுக்கவும்', 'எடு', 'பயன்படுத்தவும்', 'கொடுக்கப்பட்டது', 'செலவு', 'வெளியே', 'edukkavum', 'kuraikkavum', 'kodu'
  ]
};

const VoiceInventoryIntake = ({ inventory = [], medicines = [], onUpdateSuccess }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [language, setLanguage] = useState('en-IN'); // 'en-IN', 'hi-IN', 'ta-IN'
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [parseError, setParseError] = useState(null);
  const [speechSupported, setSpeechSupported] = useState(true);
  
  // Parsed candidate command awaiting confirmation
  const [parsedCommand, setParsedCommand] = useState(null);
  const [isSaving, setIsSaving] = useState(false);

  const recognitionRef = useRef(null);

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSpeechSupported(false);
    }
  }, []);

  const startListening = () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      alert('Speech recognition is not supported in this browser. You can type commands in the text box below.');
      return;
    }

    try {
      if (recognitionRef.current) {
        recognitionRef.current.abort();
      }

      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = language;

      recognition.onstart = () => {
        setIsListening(true);
        setParseError(null);
        setTranscript('');
        setParsedCommand(null);
      };

      recognition.onresult = (event) => {
        let currentTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          currentTranscript += event.results[i][0].transcript;
        }
        setTranscript(currentTranscript);
      };

      recognition.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        if (event.error === 'not-allowed') {
          setParseError('Microphone permission was denied. Please allow microphone access in your browser.');
        } else if (event.error === 'no-speech') {
          setParseError('No speech was detected. Please try speaking closer to the microphone.');
        } else {
          setParseError(`Speech recognition error: ${event.error}`);
        }
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      console.error('Failed to initialize speech recognition:', err);
      setIsListening(false);
      setParseError('Unable to start microphone. Please try again or type the command.');
    }
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsListening(false);
  };

  // Helper parser function
  const parseVoiceCommand = (text) => {
    if (!text || !text.trim()) {
      setParseError('Please speak or type a medicine inventory command.');
      setParsedCommand(null);
      return;
    }

    const cleanText = text.toLowerCase().trim();
    let extractedQty = null;

    // 1. Extract Quantity from digits (e.g. "10", "20 strips")
    const digitMatch = cleanText.match(/\b\d+\b/);
    if (digitMatch) {
      extractedQty = parseInt(digitMatch[0], 10);
    } else {
      // Check number words in English, Hindi, and Tamil
      for (const [word, num] of Object.entries(NUMBER_WORDS)) {
        if (cleanText.includes(word.toLowerCase())) {
          extractedQty = num;
          break;
        }
      }
    }

    if (!extractedQty || extractedQty <= 0) {
      setParseError('Could not identify a valid quantity. Example: "Add 10 Paracetamol" or "10 பாராசிட்டமால் சேர்க்கவும்"');
      setParsedCommand(null);
      return;
    }

    // 2. Extract Action (IN vs OUT)
    let extractedAction = 'IN'; // Default to IN if not specified
    let foundAction = false;

    for (const keyword of ACTION_KEYWORDS.OUT) {
      if (cleanText.includes(keyword.toLowerCase())) {
        extractedAction = 'OUT';
        foundAction = true;
        break;
      }
    }

    if (!foundAction) {
      for (const keyword of ACTION_KEYWORDS.IN) {
        if (cleanText.includes(keyword.toLowerCase())) {
          extractedAction = 'IN';
          foundAction = true;
          break;
        }
      }
    }

    // 3. Extract Medicine & Match with Centre's Inventory
    let matchedMedId = null;
    let longestMatchLen = 0;

    for (const [medIdStr, aliases] of Object.entries(MEDICINE_ALIASES)) {
      const medId = parseInt(medIdStr, 10);
      for (const alias of aliases) {
        if (cleanText.includes(alias.toLowerCase())) {
          if (alias.length > longestMatchLen) {
            longestMatchLen = alias.length;
            matchedMedId = medId;
          }
        }
      }
    }

    if (!matchedMedId) {
      setParseError('Could not detect a recognized medicine name. Please check spelling or pronounce clearly.');
      setParsedCommand(null);
      return;
    }

    // Find the item in the current centre's inventory
    const inventoryItem = inventory.find(i => i.medicine_id === matchedMedId);
    if (!inventoryItem) {
      setParseError(`Medicine ID #${matchedMedId} was recognized, but is not currently stocked in this centre's inventory.`);
      setParsedCommand(null);
      return;
    }

    // Validation for OUT exceeding stock
    if (extractedAction === 'OUT' && extractedQty > inventoryItem.current_stock) {
      setParseError(`Cannot dispense ${extractedQty} units. Current stock is only ${inventoryItem.current_stock}.`);
      setParsedCommand(null);
      return;
    }

    // Successfully parsed candidate command
    const officialName = medicines?.find(m => m.medicine_id === matchedMedId)?.medicine_name || MEDICINE_ALIASES[matchedMedId][0].toUpperCase();
    
    setParseError(null);
    setParsedCommand({
      rawText: text,
      inventoryId: inventoryItem.inventory_id,
      medicineId: matchedMedId,
      medicineName: officialName,
      quantity: extractedQty,
      action: extractedAction,
      currentStock: inventoryItem.current_stock,
      projectedStock: extractedAction === 'IN' 
        ? inventoryItem.current_stock + extractedQty 
        : inventoryItem.current_stock - extractedQty
    });
  };

  // Trigger parsing when user finishes speaking or types
  useEffect(() => {
    if (transcript && !isListening) {
      parseVoiceCommand(transcript);
    }
  }, [transcript, isListening]);

  const handleConfirmUpdate = async () => {
    if (!parsedCommand) return;
    setIsSaving(true);
    try {
      await api.put(`/inventory/${parsedCommand.inventoryId}`, {
        quantity: parsedCommand.quantity,
        transaction_type: parsedCommand.action
      });

      if (onUpdateSuccess) {
        onUpdateSuccess(`Inventory updated: ${parsedCommand.action === 'IN' ? '+' : '-'}${parsedCommand.quantity} ${parsedCommand.medicineName}`);
      }

      setIsOpen(false);
      setTranscript('');
      setParsedCommand(null);
    } catch (err) {
      console.error('Failed to confirm voice inventory update:', err);
      setParseError(err.response?.data?.detail || 'Failed to update inventory in database.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <>
      {/* Voice Intake Trigger Button */}
      <button
        onClick={() => {
          setIsOpen(true);
          setTranscript('');
          setParsedCommand(null);
          setParseError(null);
        }}
        className="inline-flex items-center px-3 py-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-sm transition focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 gap-1.5"
        title="Voice-Based Inventory Update (English, Hindi, Tamil)"
      >
        <Mic className="h-4 w-4" />
        <span>Voice Intake</span>
      </button>

      {/* Voice Modal Dialog */}
      {isOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95">
            
            {/* Modal Header */}
            <div className="px-6 py-4 bg-gradient-to-r from-indigo-600 to-indigo-700 text-white flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <div className="p-2 bg-white/10 rounded-lg">
                  <Mic className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-base font-bold">Voice Medicine Intake</h3>
                  <p className="text-xs text-indigo-100">Supports English, Hindi, and Tamil commands</p>
                </div>
              </div>
              <button 
                onClick={() => {
                  stopListening();
                  setIsOpen(false);
                }}
                className="text-indigo-200 hover:text-white transition"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="p-6 space-y-5">

              {/* Language Selection */}
              <div className="flex items-center justify-between bg-slate-50 p-3 rounded-xl border border-slate-200">
                <div className="flex items-center text-xs font-semibold text-slate-700">
                  <Languages className="h-4 w-4 text-indigo-600 mr-1.5" />
                  <span>Spoken Language:</span>
                </div>
                <div className="flex space-x-1">
                  <button
                    type="button"
                    onClick={() => setLanguage('en-IN')}
                    className={`px-2.5 py-1 text-xs font-semibold rounded-md transition ${
                      language === 'en-IN' 
                        ? 'bg-indigo-600 text-white shadow-xs' 
                        : 'text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    English
                  </button>
                  <button
                    type="button"
                    onClick={() => setLanguage('hi-IN')}
                    className={`px-2.5 py-1 text-xs font-semibold rounded-md transition ${
                      language === 'hi-IN' 
                        ? 'bg-indigo-600 text-white shadow-xs' 
                        : 'text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    हिंदी (Hindi)
                  </button>
                  <button
                    type="button"
                    onClick={() => setLanguage('ta-IN')}
                    className={`px-2.5 py-1 text-xs font-semibold rounded-md transition ${
                      language === 'ta-IN' 
                        ? 'bg-indigo-600 text-white shadow-xs' 
                        : 'text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    தமிழ் (Tamil)
                  </button>
                </div>
              </div>

              {/* Microphone Action Area */}
              <div className="flex flex-col items-center justify-center py-4 bg-slate-50 rounded-xl border border-dashed border-slate-300">
                {isListening ? (
                  <div className="flex flex-col items-center">
                    <button
                      type="button"
                      onClick={stopListening}
                      className="relative h-16 w-16 rounded-full bg-rose-500 text-white flex items-center justify-center shadow-lg hover:bg-rose-600 transition animate-pulse"
                    >
                      <Mic className="h-8 w-8" />
                      <span className="absolute -top-1 -right-1 flex h-4 w-4">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                        <span className="relative inline-flex rounded-full h-4 w-4 bg-rose-600"></span>
                      </span>
                    </button>
                    <p className="mt-3 text-xs font-bold text-rose-600 animate-bounce">
                      Listening... Speak your command now
                    </p>
                    <p className="text-[11px] text-slate-400 mt-0.5">Click mic to stop recording</p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center">
                    <button
                      type="button"
                      onClick={startListening}
                      className="h-16 w-16 rounded-full bg-indigo-600 text-white flex items-center justify-center shadow-lg hover:bg-indigo-700 transition hover:scale-105"
                    >
                      <Mic className="h-8 w-8" />
                    </button>
                    <p className="mt-3 text-xs font-bold text-slate-700">Click to Speak Command</p>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      {language === 'en-IN' ? 'e.g. "Add 10 Paracetamol" or "Remove 5 Amoxicillin"' :
                       language === 'hi-IN' ? 'उदा. "10 पैरासिटामोल जोड़ें" या "5 अमोक्सिसिलिन निकालें"' :
                       'உதா. "10 பாராசிட்டமால் சேர்க்கவும்" அல்லது "5 அமோக்சிசிலின் குறைக்கவும்"'}
                    </p>
                  </div>
                )}
              </div>

              {/* Transcript & Manual Input Area */}
              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1 flex items-center justify-between">
                  <span>Voice Transcription / Text Input</span>
                  {transcript && (
                    <button
                      type="button"
                      onClick={() => {
                        setTranscript('');
                        setParsedCommand(null);
                        setParseError(null);
                      }}
                      className="text-slate-400 hover:text-slate-600 text-[11px] font-normal flex items-center"
                    >
                      <RotateCcw className="h-3 w-3 mr-0.5" /> Clear
                    </button>
                  )}
                </label>
                <div className="relative">
                  <input
                    type="text"
                    placeholder={
                      language === 'en-IN' ? 'Type or speak: "Add 15 Metformin" / "Remove 5 ORS"...' :
                      language === 'hi-IN' ? 'टाइप या बोलें: "15 मेटफॉर्मिन जोड़ें" / "5 ओआरएस निकालें"...' :
                      'டைப் செய்யவும்: "15 மெட்பார்மின் சேர்க்கவும்"...'
                    }
                    value={transcript}
                    onChange={(e) => {
                      setTranscript(e.target.value);
                      parseVoiceCommand(e.target.value);
                    }}
                    className="w-full px-3.5 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 font-medium text-slate-800"
                  />
                </div>
              </div>

              {/* Parsing Error Display */}
              {parseError && (
                <div className="bg-rose-50 border border-rose-200 text-rose-700 p-3 rounded-lg text-xs flex items-start">
                  <AlertTriangle className="h-4 w-4 mr-2 flex-shrink-0 mt-0.5 text-rose-500" />
                  <span>{parseError}</span>
                </div>
              )}

              {/* Confirmation Card (Appears only after successful parse) */}
              {parsedCommand && (
                <div className="bg-emerald-50/80 border-2 border-emerald-500/80 rounded-xl p-4 space-y-3">
                  <div className="flex items-center justify-between pb-2 border-b border-emerald-200">
                    <div className="flex items-center space-x-1.5 text-emerald-800 font-bold text-xs">
                      <Sparkles className="h-4 w-4 text-emerald-600" />
                      <span>Extracted Command (Review before saving)</span>
                    </div>
                    <span className={`px-2 py-0.5 text-[10px] font-extrabold rounded-full ${
                      parsedCommand.action === 'IN' 
                        ? 'bg-emerald-600 text-white' 
                        : 'bg-orange-600 text-white'
                    }`}>
                      {parsedCommand.action === 'IN' ? 'ADD (IN)' : 'USE (OUT)'}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 text-xs">
                    <div className="bg-white p-2.5 rounded-lg border border-emerald-200">
                      <p className="text-[10px] text-slate-400 font-bold uppercase">Medicine</p>
                      <p className="font-bold text-slate-800 text-sm">{parsedCommand.medicineName}</p>
                      <p className="text-[10px] text-slate-400">ID #{parsedCommand.medicineId}</p>
                    </div>
                    <div className="bg-white p-2.5 rounded-lg border border-emerald-200">
                      <p className="text-[10px] text-slate-400 font-bold uppercase">Quantity</p>
                      <p className="font-bold text-emerald-700 text-sm">
                        {parsedCommand.action === 'IN' ? '+' : '-'}{parsedCommand.quantity} units
                      </p>
                      <p className="text-[10px] text-slate-500">
                        {parsedCommand.currentStock} &rarr; <strong className="text-slate-800">{parsedCommand.projectedStock}</strong>
                      </p>
                    </div>
                  </div>

                  <div className="pt-2 flex items-center justify-end space-x-2">
                    <button
                      type="button"
                      onClick={() => setParsedCommand(null)}
                      className="px-3 py-1.5 border border-slate-300 rounded-lg text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 transition"
                    >
                      Cancel
                    </button>
                    <button
                      type="button"
                      disabled={isSaving}
                      onClick={handleConfirmUpdate}
                      className="px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold shadow-sm transition flex items-center disabled:opacity-50"
                    >
                      {isSaving ? (
                        <>
                          <Loader2 className="h-3.5 w-3.5 animate-spin mr-1.5" />
                          Updating...
                        </>
                      ) : (
                        <>
                          <CheckCircle2 className="h-3.5 w-3.5 mr-1.5" />
                          Confirm & Apply Stock
                        </>
                      )}
                    </button>
                  </div>
                </div>
              )}

            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default VoiceInventoryIntake;
