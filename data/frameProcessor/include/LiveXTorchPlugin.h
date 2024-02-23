    #ifndef FRAMEPROCESSOR_LiveXTorchPlugin_H_
#define FRAMEPROCESSOR_LiveXTorchPlugin_H_

#include <torch/script.h>
#include <torch/torch.h>

#include <log4cxx/logger.h>
#include <log4cxx/basicconfigurator.h>
#include <log4cxx/propertyconfigurator.h>
#include <log4cxx/helpers/exception.h>
#include <string>
using namespace log4cxx;
using namespace log4cxx::helpers;

#include <boost/shared_ptr.hpp>
#include <boost/scoped_ptr.hpp>

#include "FrameProcessorPlugin.h"
#include "ClassLoader.h"

namespace FrameProcessor
{

    class LiveXTorchPlugin : public FrameProcessorPlugin
    {
        public:

            LiveXTorchPlugin();
            virtual ~LiveXTorchPlugin();

            void process_frame(boost::shared_ptr<Frame> frame);
            void configure(OdinData::IpcMessage& config, OdinData::IpcMessage& reply);

            int get_version_major();
            int get_version_minor();
            int get_version_patch();
            std::string get_version_short();
            std::string get_version_long();

            
            
            
            virtual void status(OdinData::IpcMessage& status);
            virtual bool reset_statistics(void);

            
            // bool loadModel(std::string file_name);

            

        
        private:

            virtual void requestConfiguration(OdinData::IpcMessage& reply);
            void decodeHeader(boost::shared_ptr<Frame> frame);
            void loadModel(std::string path, bool gpu_avail);

            std::string model_path;
            std::string preprocessor_path;
            std::vector<long int> frame_dimensions;
            torch::jit::Module model;
            torch::jit::Module preprocessor;

            bool model_loaded;
            bool preprocessor_loaded;
            bool decode_header;

            static const std::string CONFIG_MODEL_PATH;
            static const std::string CONFIG_PREPROCESSOR_PATH;
            static const std::string CONFIG_DECODE_HEADER;

            LoggerPtr logger_;
    };

    REGISTER(FrameProcessorPlugin, LiveXTorchPlugin, "LiveXTorchPlugin");
}

namespace LiveX
{
    typedef struct //stolen from Inaira
    {
        uint32_t frame_number;
        // uint32_t frame_state;
        // uint64_t frame_start_time_secs;
        // uint64_t frame_start_nsecs;
        uint32_t frame_width;
        uint32_t frame_height;
        uint32_t frame_data_type;
        uint32_t frame_size;
    } FrameHeader;
    
}

#endif /*FRAMEPROCESSOR_LiveXTorchPlugin_H_*/